from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.domain import ModerationDecision
from app.inference.pipeline import load_text_classifier


class TextInferenceService(Protocol):
    def classify_text(self, text: str) -> ModerationDecision:
        ...


@dataclass(frozen=True)
class ToxicOrNotInferenceService(TextInferenceService):
    model: object
    threshold: float

    @classmethod
    def from_artifacts(
        cls,
        artifacts_path: str | Path,
        *,
        threshold: float,
        w2v_model_path: str | Path,
        w2v_format: str,
        w2v_stem: bool,
    ) -> ToxicOrNotInferenceService:
        model = load_text_classifier(
            artifacts_path,
            w2v_model_path=w2v_model_path,
            w2v_format=w2v_format,
            stem=w2v_stem,
        )
        return cls(model=model, threshold=threshold)

    def classify_text(self, text: str) -> ModerationDecision:
        normalized = str(text or "").strip()
        if not normalized:
            return ModerationDecision(status="approved", reason="empty_text")

        proba = float(self.model.predict_proba([normalized])[0][1])
        toxic = proba >= self.threshold
        status = "rejected" if toxic else "approved"
        reason = f"toxicornot: toxic_proba={proba:.4f} threshold={self.threshold:.2f}"
        print(  # noqa: T201
            f"[ToxicOrNotInferenceService] classify_text: text={normalized!r} "
            f"proba={proba:.4f} threshold={self.threshold:.2f} status={status}"
        )
        return ModerationDecision(status=status, reason=reason)
