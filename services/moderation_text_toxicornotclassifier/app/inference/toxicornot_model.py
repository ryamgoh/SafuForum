from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class ToxicityModel:
    """
    Deprecated wrapper kept for legacy imports.

    Prefer using `app.inference.service.ToxicOrNotInferenceService` or
    `app.inference.pipeline.load_text_classifier()` directly.
    """

    pipeline: object

    def predict_proba(self, texts: Sequence[str]) -> np.ndarray:
        proba = self.pipeline.predict_proba(list(texts))
        return np.asarray(proba)[:, 1]

    def predict(self, texts: Sequence[str], *, threshold: float = 0.5) -> np.ndarray:
        return (self.predict_proba(texts) >= threshold).astype(int)


def load_model(artifacts_path: str | Path) -> ToxicityModel:
    raise RuntimeError(
        "load_model() now requires explicit Word2Vec config. "
        "Use app.inference.pipeline.load_text_classifier(..., w2v_model_path=..., stem=..., w2v_format=...) instead."
    )
