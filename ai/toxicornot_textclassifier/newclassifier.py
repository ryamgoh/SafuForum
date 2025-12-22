#!/usr/bin/env python3

import argparse
import os
from collections import Counter
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from gensim.models import KeyedVectors, Word2Vec
from gensim.parsing.porter import PorterStemmer
from gensim.parsing.preprocessing import remove_stopwords
from gensim.utils import simple_preprocess
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

TOXICITY_COLUMNS = (
    "toxic",
    "severe_toxic",
    "obscene",
    "threat",
    "insult",
    "identity_hate",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Binary toxic/not-toxic classifier for the Kaggle Jigsaw dataset using averaged Word2Vec vectors."
    )
    parser.add_argument(
        "--train-csv", default="result/train.csv", help="Path to Kaggle train.csv"
    )
    parser.add_argument(
        "--test-size", type=float, default=0.30, help="Holdout fraction"
    )
    parser.add_argument("--random-state", type=int, default=15, help="Random seed")
    parser.add_argument(
        "--train-full",
        action="store_true",
        help="Train on all rows and skip holdout evaluation.",
    )

    parser.add_argument(
        "--vector-size", type=int, default=200, help="Word2Vec vector size"
    )
    parser.add_argument("--window", type=int, default=3, help="Word2Vec context window")
    parser.add_argument("--min-count", type=int, default=1, help="Word2Vec min_count")
    parser.add_argument(
        "--sg", type=int, default=1, choices=(0, 1), help="0=CBOW, 1=skip-gram"
    )
    parser.add_argument(
        "--workers", type=int, default=os.cpu_count() or 1, help="Word2Vec workers"
    )
    parser.add_argument(
        "--w2v-model",
        default=None,
        help="Path to saved embeddings; default is result/word2vec_<vector-size>.model (or .kv if --w2v-format=vectors).",
    )
    parser.add_argument(
        "--retrain-w2v",
        action="store_true",
        help="Force training a fresh Word2Vec model",
    )
    parser.add_argument(
        "--w2v-format",
        choices=("full", "vectors"),
        default="full",
        help="How to persist embeddings: full=Word2Vec model (includes training state, larger) or vectors=KeyedVectors only (smaller, inference-only).",
    )
    parser.add_argument("--no-stem", action="store_true", help="Disable stemming")

    parser.add_argument(
        "--oversample",
        action="store_true",
        help="Randomly oversample the minority class on the training vectors (disables class_weight).",
    )
    parser.add_argument(
        "--artifacts-out",
        default="results/toxic_logreg.joblib",
        help="Path to save classifier artifacts (joblib) for serving.",
    )
    parser.add_argument(
        "--no-save", action="store_true", help="Do not save classifier artifacts."
    )
    return parser.parse_args()


def make_binary_label(df: pd.DataFrame) -> np.ndarray:
    missing = [c for c in TOXICITY_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing toxicity columns: {missing}")
    return df[list(TOXICITY_COLUMNS)].max(axis=1).astype(int).to_numpy()


def preprocess_texts(texts: pd.Series, *, stem: bool) -> list[list[str]]:
    """
    Preprocess texts by removing stop-words, and ensuring lower-case.
    Optionally, a stemmer can be use to convert words into their base form (i.e. "Works" -> "Work")
    """
    stemmer = None if not stem else PorterStemmer()
    processed: list[list[str]] = []
    for raw in texts.astype(str).fillna(""):
        cleaned = remove_stopwords(raw)
        tokens = simple_preprocess(cleaned, deacc=True)
        if stemmer is not None:
            tokens = [stemmer.stem(tok) for tok in tokens]
        processed.append(tokens)
    return processed


def load_or_train_w2v(
    sentences: list[list[str]],
    *,
    model_path: Path,
    vector_size: int,
    window: int,
    min_count: int,
    workers: int,
    sg: int,
    seed: int,
    retrain: bool,
    persist_format: str,
) -> KeyedVectors:
    if model_path.exists() and not retrain:
        return _load_embeddings(model_path)

    model_path.parent.mkdir(parents=True, exist_ok=True)
    model = Word2Vec(
        sentences=sentences,
        vector_size=vector_size,
        window=window,
        min_count=min_count,
        workers=workers,
        sg=sg,
        seed=seed,
    )
    if persist_format == "vectors":
        model.wv.save(str(model_path))
        return model.wv

    model.save(str(model_path))
    return model.wv


def _load_embeddings(path: Path) -> KeyedVectors:
    obj = Word2Vec.load(str(path))
    if isinstance(obj, Word2Vec):
        return obj.wv
    if isinstance(obj, KeyedVectors):
        return obj
    raise TypeError(f"Unsupported embeddings object in {path}: {type(obj)!r}")


def document_vector(tokens: list[str], model: KeyedVectors) -> np.ndarray:
    vectors = [model[tok] for tok in tokens if tok in model]
    if not vectors:
        return np.zeros(model.vector_size, dtype=np.float32)
    return np.mean(np.asarray(vectors, dtype=np.float32), axis=0)


def build_matrix(token_lists: list[list[str]], model: KeyedVectors) -> np.ndarray:
    return np.vstack([document_vector(tokens, model) for tokens in token_lists]).astype(
        np.float32, copy=False
    )


def save_artifacts(
    path: Path, *, classifier: LogisticRegression, w2v_model_path: Path, stem: bool, w2v_format: str
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "classifier": classifier,
            "w2v_model_path": str(w2v_model_path),
            "stem": stem,
            "w2v_format": str(w2v_format),
        },
        str(path),
    )


def main() -> int:
    args = parse_args()

    w2v_model_path = Path(args.w2v_model) if args.w2v_model else Path(
        f"result/word2vec_{args.vector_size}.kv" if args.w2v_format == "vectors" else f"result/word2vec_{args.vector_size}.model"
    )

    df = pd.read_csv(args.train_csv, usecols=["comment_text", *TOXICITY_COLUMNS])
    y = make_binary_label(df)

    token_lists = preprocess_texts(df["comment_text"], stem=not args.no_stem)

    if args.train_full:
        X_train_tokens, y_train = token_lists, y
        X_test_tokens, y_test = None, None
    else:
        X_train_tokens, X_test_tokens, y_train, y_test = train_test_split(
            token_lists,
            y,
            test_size=args.test_size,
            random_state=args.random_state,
            shuffle=True,
            stratify=y,
        )

    w2v = load_or_train_w2v(
        X_train_tokens,
        model_path=w2v_model_path,
        vector_size=args.vector_size,
        window=args.window,
        min_count=args.min_count,
        workers=args.workers,
        sg=args.sg,
        seed=args.random_state,
        retrain=args.retrain_w2v,
        persist_format=args.w2v_format,
    )

    X_train_vec = build_matrix(X_train_tokens, w2v)
    X_test_vec = None if X_test_tokens is None else build_matrix(X_test_tokens, w2v)

    if args.oversample:
        from imblearn.over_sampling import RandomOverSampler

        ros = RandomOverSampler(random_state=args.random_state)
        X_train_vec, y_train = ros.fit_resample(X_train_vec, y_train)
        class_weight = None
    else:
        class_weight = "balanced"

    clf = LogisticRegression(
        max_iter=1000,
        solver="saga",
        n_jobs=-1,
        random_state=args.random_state,
        class_weight=class_weight,
    )
    clf.fit(X_train_vec, y_train)

    if not args.no_save and args.artifacts_out:
        save_artifacts(
            Path(args.artifacts_out),
            classifier=clf,
            w2v_model_path=w2v_model_path,
            stem=not args.no_stem,
            w2v_format=args.w2v_format,
        )
        print(f"Saved classifier artifacts to: {args.artifacts_out}")
        print()

    if args.train_full:
        print("Trained on full dataset (no holdout evaluation).")
        print("Train label counts:", Counter(y_train))
        return 0

    y_pred = clf.predict(X_test_vec)
    print("True label counts:", Counter(y_test))
    print("Pred label counts:", Counter(y_pred))
    print()
    print(classification_report(y_test, y_pred, digits=3)) 
    print("Confusion matrix (rows=true, cols=pred):")
    print(confusion_matrix(y_test, y_pred))

    if hasattr(clf, "predict_proba"):
        y_score = clf.predict_proba(X_test_vec)[:, 1]
        print()
        print(f"ROC AUC: {roc_auc_score(y_test, y_score):.4f}")
        print(f"PR  AUC: {average_precision_score(y_test, y_score):.4f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
