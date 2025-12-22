import logging
import threading
import docker

LOGGER = logging.getLogger(__name__)


class DockerRegistry:
    def __init__(self, docker_url="tcp://docker-socket-proxy:2375"):
        self.client = docker.DockerClient(base_url=docker_url)
        self.label_filter = {"label": "domain=moderation"}
        self._active_count = 0
        self._lock = threading.Lock()

        # 1. Initial sync
        self._sync_count()

        # 2. Start background event listener
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._listen_for_events, daemon=True)
        self._thread.start()

    def _sync_count(self):
        """Query Docker API for all currently running moderation containers."""
        with self._lock:
            containers = self.client.containers.list(filters=self.label_filter)
            self._active_count = len(containers)
            LOGGER.info("Docker Registry synced. Active moderators: %s", self._active_count)

    def _listen_for_events(self):
        """Listen to Docker events (start, die, pause, unpause)."""
        # filters={'event': ['start', 'die', 'pause', 'unpause']}
        for event in self.client.events(decode=True, filters=self.label_filter):
            if self._stop_event.is_set():
                break
            
            action = event.get("action")
            if action in ("start", "unpause"):
                with self._lock:
                    self._active_count += 1
            elif action in ("die", "pause"):
                with self._lock:
                    self._active_count = max(0, self._active_count - 1)
            
            LOGGER.info("Docker Event: %s. New count: %s", action, self._active_count)

    @property
    def current_count(self) -> int:
        with self._lock:
            # Fallback: if count is 0, re-sync once just in case
            if self._active_count == 0:
                self._sync_count()
            return self._active_count