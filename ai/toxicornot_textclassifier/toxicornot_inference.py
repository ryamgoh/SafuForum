#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import joblib
import numpy as np
from gensim.models import KeyedVectors, Word2Vec
from gensim.parsing.porter import PorterStemmer
from gensim.parsing.preprocessing import remove_stopwords
from gensim.utils import simple_preprocess


@dataclass(frozen=True)
class ToxicityModel:
    classifier: object
    w2v: KeyedVectors
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
        "Could not find embeddings referenced by artifacts. "
        f"Stored path={stored_path!r}; tried: {tried}. "
        "Make sure you deploy the embeddings file AND its companion .npy file(s)."
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
    w2v = _load_embeddings(w2v_path)

    return ToxicityModel(classifier=bundle["classifier"], w2v=w2v, stem=bool(bundle["stem"]))


def _load_embeddings(path: Path) -> KeyedVectors:
    obj = Word2Vec.load(str(path))
    if isinstance(obj, Word2Vec):
        return obj.wv
    if isinstance(obj, KeyedVectors):
        return obj
    raise TypeError(f"Unsupported embeddings object in {path}: {type(obj)!r}")


def preprocess_text(text: str, *, stemmer: PorterStemmer | None) -> list[str]:
    cleaned = remove_stopwords(str(text or ""))
    tokens = simple_preprocess(cleaned, deacc=True)
    if stemmer is None:
        return tokens
    return [stemmer.stem(tok) for tok in tokens]


def document_vector(tokens: list[str], model: KeyedVectors) -> np.ndarray:
    vectors = [model[tok] for tok in tokens if tok in model]
    if not vectors:
        return np.zeros(model.vector_size, dtype=np.float32)
    return np.mean(np.asarray(vectors, dtype=np.float32), axis=0)


def build_matrix(texts: Sequence[str], model: KeyedVectors, *, stem: bool) -> np.ndarray:
    stemmer = PorterStemmer() if stem else None
    rows = [document_vector(preprocess_text(text, stemmer=stemmer), model) for text in texts]
    if not rows:
        return np.zeros((0, model.vector_size), dtype=np.float32)
    return np.vstack(rows).astype(np.float32, copy=False)


def _iter_texts_from_args(args: argparse.Namespace) -> list[str]:
    texts: list[str] = []

    if args.text:
        texts.extend(args.text)

    if args.file:
        lines = Path(args.file).read_text(encoding="utf-8").splitlines()
        texts.extend([line for line in lines if line.strip()])

    if args.stdin:
        texts.extend([line.rstrip("\n") for line in sys.stdin if line.strip()])

    return texts


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run toxicity inference with saved artifacts.")
    parser.add_argument("--artifacts", default="results/toxic_logreg.joblib", help="Path to .joblib artifacts")
    parser.add_argument("--threshold", type=float, default=0.5, help="Classification threshold")

    group = parser.add_argument_group("Input")
    group.add_argument("--text", action="append", help="Text to score (repeatable)")
    group.add_argument("--file", help="UTF-8 file with one text per line")
    group.add_argument("--stdin", action="store_true", help="Read texts from stdin (one per line)")

    out = parser.add_argument_group("Output")
    out.add_argument("--jsonl", action="store_true", help="Output JSON Lines")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    texts = _iter_texts_from_args(args)
    if not texts:
        raise SystemExit("No input provided. Use --text, --file, or --stdin.")

    model = load_model(args.artifacts)
    probs = model.predict_proba(texts)
    labels = (probs >= args.threshold).astype(int)

    if args.jsonl:
        for text, prob, label in zip(texts, probs.tolist(), labels.tolist(), strict=False):
            print(json.dumps({"toxic": int(label), "toxic_proba": float(prob), "text": text}, ensure_ascii=False))
        return 0

    for text, prob, label in zip(texts, probs.tolist(), labels.tolist(), strict=False):
        print(f"toxic={int(label)} proba={prob:.4f} text={text}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
