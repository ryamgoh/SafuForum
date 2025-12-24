import logging
import threading
import docker

LOGGER = logging.getLogger(__name__)


class DockerRegistry:
    def __init__(self, 
                 docker_url: str = "tcp://docker-socket-proxy:2375", 
                 label="domain=moderation", 
                 tls_config=None):
        # NOTE: This client connects to an internal docker-socket-proxy, which is expected
        # to be reachable only on a protected network and to enforce its own access controls.
        # For deployments that require end-to-end TLS/authentication from this service to
        # the proxy, pass a docker.tls.TLSConfig instance via tls_config.
        self.client = docker.DockerClient(base_url=docker_url, tls=tls_config)
        self.label_filter = {"label": label}
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
        """
        Listen to Docker events (start, die, pause, unpause).
        
        TODO:
        The Docker registry synchronization relies on event streaming without any error recovery mechanism. If the event stream breaks (line 33), the method silently exits when _stop_event is set, but network errors or API failures could cause the event stream to terminate unexpectedly without updating _stop_event. Consider adding error handling and reconnection logic to maintain accurate container counts.

        """
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