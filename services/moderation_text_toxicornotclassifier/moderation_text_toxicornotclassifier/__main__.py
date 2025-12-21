from __future__ import annotations

import logging
import signal

from moderation_text_toxicornotclassifier.events.rabbitmq import RabbitMQEventLoop
from moderation_text_toxicornotclassifier.events.service import ModerationEventService
from moderation_text_toxicornotclassifier.inference.service import ToxicOrNotInferenceService
from moderation_text_toxicornotclassifier.settings import load_settings


def _install_signal_handlers() -> None:
    def _handle_sigterm(signum: int, frame: object) -> None:  # pragma: no cover
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, _handle_sigterm)


def main() -> int:
    _install_signal_handlers()

    settings = load_settings()
    try:
        log_level = int(settings.log_level)
    except ValueError:
        log_level = logging.getLevelNamesMapping().get(settings.log_level.upper(), logging.INFO)
    logging.basicConfig(level=log_level)

    logger = logging.getLogger("moderation_text_toxicornotclassifier")
    logger.info("Loading model artifacts from %s", settings.model_artifacts_path)
    inference_service = ToxicOrNotInferenceService.from_artifacts(
        settings.model_artifacts_path,
        threshold=settings.toxic_threshold,
    )

    event_service = ModerationEventService(inference_service)
    return RabbitMQEventLoop(settings, event_service).run_forever()


if __name__ == "__main__":
    raise SystemExit(main())
