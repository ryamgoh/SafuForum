from __future__ import annotations

import logging
import threading
import time

import docker

LOGGER = logging.getLogger(__name__)

DEFAULT_MODERATION_TYPE_LABEL_KEY = "moderation.type"

class DockerRegistry:
    def __init__(self, 
                 docker_url: str = "tcp://docker-socket-proxy:2375", 
                 label="domain=moderation", 
                 *,
                 moderation_type_label_key: str = DEFAULT_MODERATION_TYPE_LABEL_KEY,
                 tls_config=None):
        # NOTE: This client connects to an internal docker-socket-proxy, which is expected
        # to be reachable only on a protected network and to enforce its own access controls.
        # For deployments that require end-to-end TLS/authentication from this service to
        # the proxy, pass a docker.tls.TLSConfig instance via tls_config.
        self.client = docker.DockerClient(base_url=docker_url, tls=tls_config)
        self.label_filter = {"label": label}
        self.moderation_type_label_key = moderation_type_label_key
        self._active_count = 0
        self._active_count_by_type: dict[str, int] = {}
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
            by_type: dict[str, int] = {}
            for container in containers:
                labels = getattr(container, "labels", None) or {}
                raw_type = labels.get(self.moderation_type_label_key)
                if raw_type is None:
                    continue
                moderation_type = str(raw_type).strip().lower()
                if not moderation_type:
                    continue
                by_type[moderation_type] = by_type.get(moderation_type, 0) + 1
            self._active_count_by_type = by_type
            LOGGER.info("Docker Registry synced. Active moderators: %s", self._active_count)

    def _listen_for_events(self):
        """
        Listen to Docker events (start, die, pause, unpause).
        
        """
        while not self._stop_event.is_set():
            try:
                for event in self.client.events(decode=True, filters=self.label_filter):
                    if self._stop_event.is_set():
                        break

                    action = event.get("action")
                    if action in ("start", "die", "pause", "unpause", "stop", "destroy"):
                        self._sync_count()
                        LOGGER.info(
                            "Docker Event: %s. New count: %s", action, self._active_count
                        )
            except Exception as exc:
                # Event stream can drop; resync and retry with a small backoff.
                LOGGER.warning("Docker event stream error; resyncing: %s", exc)
                try:
                    self._sync_count()
                except Exception:
                    LOGGER.exception("Failed to resync Docker Registry after stream error.")
                time.sleep(5)

    @property
    def current_count(self) -> int:
        with self._lock:
            # Fallback: if count is 0, re-sync once just in case
            if self._active_count == 0:
                self._sync_count()
            return self._active_count

    def count_for_type(self, moderation_type: str | None) -> int:
        if moderation_type is None:
            return self.current_count

        normalized = str(moderation_type).strip().lower()
        if not normalized:
            return self.current_count

        with self._lock:
            count = self._active_count_by_type.get(normalized, 0)

        if count == 0:
            # Fallback: resync once in case events were missed.
            self._sync_count()
            with self._lock:
                count = self._active_count_by_type.get(normalized, 0)

        return count
