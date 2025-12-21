from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from moderation_text_toxicornotclassifier.domain import ModerationDecision
from moderation_text_toxicornotclassifier.inference.toxicornot_model import ToxicityModel, load_model


class TextInferenceService(Protocol):
    def classify_text(self, text: str) -> ModerationDecision: ...


@dataclass(frozen=True)
class ToxicOrNotInferenceService(TextInferenceService):
    model: ToxicityModel
    threshold: float

    @classmethod
    def from_artifacts(cls, artifacts_path: str | Path, *, threshold: float) -> ToxicOrNotInferenceService:
        model = load_model(artifacts_path)
        return cls(model=model, threshold=threshold)

    def classify_text(self, text: str) -> ModerationDecision:
        normalized = str(text or "").strip()
        if not normalized:
            return ModerationDecision(status="approved", reason="empty_text")

        proba = float(self.model.predict_proba([normalized])[0])
        toxic = proba >= self.threshold
        status = "rejected" if toxic else "approved"
        reason = f"toxicornot: toxic_proba={proba:.4f} threshold={self.threshold:.2f}"
        return ModerationDecision(status=status, reason=reason)

