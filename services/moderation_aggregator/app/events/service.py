from __future__ import annotations

from dataclasses import dataclass
import logging
import json
from typing import Optional
import redis
from app.settings import Settings
from app.domain import JobCompletedEvent, ResultEvent, Status
from app.events.docker_registry import DockerRegistry


@dataclass(frozen=True)
class ProcessedEvent:
    completion: JobCompletedEvent
    correlation_id: str | None

LOGGER = logging.getLogger(__name__)

# KEYS[1] -> 'agg:{correlation_id}:count'
# ARGV[1] -> registry.current_count (the expected number of workers)
# ARGV[2] -> expiry in seconds (e.g., 3600)
LUA_INITIALIZE_AND_DECR = """
local current = redis.call('get', KEYS[1])
if not current then
    -- First time seeing this job: set the expected count from the Docker Registry
    redis.call('set', KEYS[1], ARGV[1])
    redis.call('expire', KEYS[1], ARGV[2])
end
-- Decrement and return the new value
return redis.call('decr', KEYS[1])
"""


class EventService:
    def __init__(self, settings: Settings, registry: DockerRegistry):
        self.settings = settings
        self.registry = registry
        self.redis = redis.Redis(
            host=settings.redis_host, 
            decode_responses=True
        )
        # Pre-register the script for performance
        self._lua_script = self.redis.register_script(LUA_INITIALIZE_AND_DECR)

    def handle_message(
        self,
        body: bytes,
        correlation_id: str | None,
        *,
        service_name: str | None = None,
    ) -> Optional[JobCompletedEvent]:
        try:
            raw_data = json.loads(body.decode("utf-8"))
            if isinstance(raw_data, dict) and service_name:
                raw_data.setdefault("service_name", service_name)
            result = ResultEvent.model_validate(raw_data)
        except Exception as e:
            LOGGER.error("Failed to parse inbound event: %s", e)
            return None

        correlation_id = str(correlation_id) if correlation_id else None
        if not correlation_id:
            if result.moderation_job_id is None:
                LOGGER.error("Dropping result event with no correlation_id or moderation_job_id")
                return None
            correlation_id = str(result.moderation_job_id)

        if not result.service_name:
            LOGGER.error("Dropping result event with no service_name; correlation_id=%s", correlation_id)
            return None

        count_key = f"agg:{correlation_id}:count"
        data_key = f"agg:{correlation_id}:data"

        # 1. Get the current snapshot of active workers from Docker API
        expected_workers = self.registry.current_count
        
        # 2. Atomic Update: Init if missing, then Decrement
        # We pass 3600 as the TTL for the aggregation state
        remaining = self._lua_script(keys=[count_key], args=[expected_workers, 3600])

        # 3. Store this specific service's result data
        # We use a hash to keep track of individual statuses for final decision
        self.redis.hset(data_key, result.service_name, result.status)
        self.redis.expire(data_key, 3600)

        LOGGER.info("Job %s: %s services remaining", correlation_id, remaining)

        # 4. Finalize if we hit zero
        if remaining == 0:
            return self._finalize(correlation_id, data_key, result)
        
        return None

    def _finalize(self, correlation_id: str, data_key: str, last_result: ResultEvent) -> JobCompletedEvent:
        all_results = self.redis.hgetall(data_key)
        self.redis.delete(data_key)  # Cleanup results hash
        count_key = f"agg:{correlation_id}:count"
        self.redis.delete(count_key)  # Cleanup counter key

        # Logic: If any worker rejected, the whole post is rejected
        statuses = set(all_results.values())
        
        final_status = Status.APPROVED
        if Status.REJECTED in statuses:
            final_status = Status.REJECTED
        elif Status.FAILED in statuses:
            final_status = Status.FAILED

        return JobCompletedEvent(
            moderation_job_id=last_result.moderation_job_id or correlation_id,
            post_id=last_result.post_id,
            post_version=last_result.post_version,
            status=final_status,
            reason=f"Aggregated from {len(all_results)} workers."
        )
