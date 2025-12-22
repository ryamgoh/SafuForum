import logging
import signal
import sys
from app.events.rabbitmq import RabbitMQEventLoop
from app.events.service import EventService
from app.events.docker_registry import DockerRegistry
from app.settings import settings

def _install_signal_handlers() -> None:
    """Ensures Docker/K8s 'SIGTERM' is treated like a graceful Ctrl+C."""
    def _handle_exit(signum: int, frame: object) -> None:
        # Raising KeyboardInterrupt triggers 'finally' blocks in the event loop
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, _handle_exit)
    signal.signal(signal.SIGINT, _handle_exit)

def main() -> int:
    """Main entry point for the Moderation Aggregator Service."""
    _install_signal_handlers()
   
    # 1. Load Configuration    # 2. Setup Logging
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    logger = logging.getLogger(__name__)
    
    registry = DockerRegistry(settings.docker_host)

    try:
        # 2. Initialize Services
        event_service = EventService(settings, registry)
        worker = RabbitMQEventLoop(settings, event_service)

        logger.info("Starting %s...", settings.service_name)
        return worker.run_forever()

    except KeyboardInterrupt:
        logger.info("Shutdown signal received. Closing gracefully...")
        return 0
    except RuntimeError:
        logger.exception("Runtime error in main loop")
        return 1

if __name__ == "__main__":
    sys.exit(main())
