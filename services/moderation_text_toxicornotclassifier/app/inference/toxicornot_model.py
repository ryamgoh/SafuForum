from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import joblib
import numpy as np
from gensim.models import Word2Vec
from gensim.parsing.porter import PorterStemmer
from gensim.parsing.preprocessing import remove_stopwords
from gensim.utils import simple_preprocess


@dataclass(frozen=True)
class ToxicityModel:
    classifier: object
    w2v: Word2Vec
    stem: bool

    def predict_proba(self, texts: Sequence[str]) -> np.ndarray:
        X = build_matrix(texts, self.w2v, stem=self.stem)
        proba = self.classifier.predict_proba(X)
        return np.asarray(proba)[:, 1]

    def predict(self, texts: Sequence[str], *, threshold: float = 0.5) -> np.ndarray:
        return (self.predict_proba(texts) >= threshold).astype(int)


def _resolve_w2v_path(artifacts_path: Path, stored_path: str) -> Path:
    raw_path = Path(stored_path)
    candidates: list[Path] = []

    if raw_path.is_absolute():
        candidates.append(raw_path)
    else:
        candidates.append(raw_path)
        candidates.append(artifacts_path.parent / raw_path)
        candidates.append(artifacts_path.parent / raw_path.name)

    for candidate in candidates:
        if candidate.exists():
            return candidate

    tried = ", ".join(str(p) for p in candidates)
    raise FileNotFoundError(
        "Could not find Word2Vec model referenced by artifacts. "
        f"Stored path={stored_path!r}; tried: {tried}. "
        "Make sure you deploy the .model file AND its companion .npy files."
    )


def load_model(artifacts_path: str | Path) -> ToxicityModel:
    artifacts_path = Path(artifacts_path)
    bundle = joblib.load(str(artifacts_path))

    if not isinstance(bundle, dict):
        raise TypeError(f"Expected a dict in {artifacts_path}, got {type(bundle)!r}")

    for key in ("classifier", "w2v_model_path", "stem"):
        if key not in bundle:
            raise KeyError(f"Missing key {key!r} in {artifacts_path}")

    w2v_path = _resolve_w2v_path(artifacts_path, str(bundle["w2v_model_path"]))
    w2v = Word2Vec.load(str(w2v_path))

    return ToxicityModel(classifier=bundle["classifier"], w2v=w2v, stem=bool(bundle["stem"]))


def preprocess_text(text: str, *, stemmer: PorterStemmer | None) -> list[str]:
    cleaned = remove_stopwords(str(text or ""))
    tokens = simple_preprocess(cleaned, deacc=True)
    if stemmer is None:
        return tokens
    return [stemmer.stem(tok) for tok in tokens]


def document_vector(tokens: list[str], model: Word2Vec) -> np.ndarray:
    vectors = [model.wv[tok] for tok in tokens if tok in model.wv]
    if not vectors:
        return np.zeros(model.vector_size, dtype=np.float32)
    return np.mean(np.asarray(vectors, dtype=np.float32), axis=0)


def build_matrix(texts: Sequence[str], model: Word2Vec, *, stem: bool) -> np.ndarray:
    stemmer = PorterStemmer() if stem else None
    rows = [document_vector(preprocess_text(text, stemmer=stemmer), model) for text in texts]
    if not rows:
        return np.zeros((0, model.vector_size), dtype=np.float32)
    return np.vstack(rows).astype(np.float32, copy=False)
