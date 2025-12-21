from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import joblib
import numpy as np
from gensim.models import KeyedVectors, Word2Vec
from gensim.parsing.porter import PorterStemmer
from gensim.parsing.preprocessing import remove_stopwords
from gensim.utils import simple_preprocess
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline


class Word2VecMeanVectorizer(BaseEstimator, TransformerMixin):
    def __init__(self, *, w2v_model_path: str | Path, stem: bool, w2v_format: str = "vectors") -> None:
        self.w2v_model_path = str(w2v_model_path)
        self.stem = bool(stem)
        self.w2v_format = str(w2v_format)
        self._w2v: KeyedVectors | None = None

    def fit(self, X: Any, y: Any = None) -> Word2VecMeanVectorizer:
        return self

    def transform(self, X: Iterable[str]) -> np.ndarray:
        w2v = self._load_w2v()
        stemmer = PorterStemmer() if self.stem else None
        vectors = [_document_vector(_preprocess_text(text, stemmer=stemmer), w2v) for text in X]
        if not vectors:
            return np.zeros((0, w2v.vector_size), dtype=np.float32)
        return np.vstack(vectors).astype(np.float32, copy=False)

    def _load_w2v(self) -> KeyedVectors:
        if self._w2v is None:
            self._w2v = _load_embeddings(self.w2v_model_path, w2v_format=getattr(self, "w2v_format", "vectors"))
        return self._w2v


def _preprocess_text(text: str, *, stemmer: PorterStemmer | None) -> list[str]:
    cleaned = remove_stopwords(str(text or ""))
    tokens = simple_preprocess(cleaned, deacc=True)
    if stemmer is None:
        return tokens
    return [stemmer.stem(tok) for tok in tokens]


def _document_vector(tokens: list[str], model: KeyedVectors) -> np.ndarray:
    vectors = [model[tok] for tok in tokens if tok in model]
    if not vectors:
        return np.zeros(model.vector_size, dtype=np.float32)
    return np.mean(np.asarray(vectors, dtype=np.float32), axis=0)


def _load_embeddings(path: str | Path, *, w2v_format: str) -> KeyedVectors:
    fmt = str(w2v_format or "").strip().lower()
    if fmt in {"vectors", "kv", "keyedvectors"}:
        return KeyedVectors.load(str(path), mmap="r")
    if fmt in {"full", "model", "word2vec"}:
        return Word2Vec.load(str(path), mmap="r").wv
    raise ValueError(f"Unsupported W2V_FORMAT {w2v_format!r}; expected 'vectors' or 'full'")


def load_text_classifier(
    artifacts_path: str | Path,
    *,
    w2v_model_path: str | Path,
    stem: bool,
    w2v_format: str = "vectors",
) -> Pipeline:
    """
    Loads a text->probability classifier from disk.

    Expects:
    - `artifacts_path`: a joblib-pickled sklearn classifier with `predict_proba`.
    - `w2v_model_path`: a gensim embeddings file (KeyedVectors or Word2Vec model).
    """
    obj = joblib.load(str(artifacts_path))

    classifier = obj.get("classifier") if isinstance(obj, dict) else obj
    if classifier is None:
        raise TypeError(f"Unsupported artifacts format in {artifacts_path}: {type(obj)!r}")
    if not hasattr(classifier, "predict_proba"):
        raise TypeError(
            f"Unsupported classifier in {artifacts_path}: {type(classifier)!r} (missing predict_proba)"
        )

    resolved_w2v_path = _resolve_w2v_path(Path(artifacts_path), str(w2v_model_path))
    vectorizer = Word2VecMeanVectorizer(
        w2v_model_path=str(resolved_w2v_path),
        stem=bool(stem),
        w2v_format=str(w2v_format),
    )
    return Pipeline([("w2v", vectorizer), ("clf", classifier)])


def _resolve_w2v_path(artifacts_path: Path, configured_path: str) -> Path:
    raw_path = Path(configured_path)
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
        "Could not find the configured embeddings file. "
        f"Configured path={configured_path!r}; tried: {tried}. "
        "Make sure you deploy the embeddings file AND its companion .npy file(s) next to it."
    )
