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

AGG_TTL_SECONDS = 3600

#
# Idempotent aggregation update.
#
# KEYS[1] -> 'agg:{correlation_id}:count'
# KEYS[2] -> 'agg:{correlation_id}:data'
# ARGV[1] -> registry.current_count (the expected number of workers)
# ARGV[2] -> expiry in seconds (e.g., 3600)
# ARGV[3] -> service_name
# ARGV[4] -> status
#
# Only decrements the counter when the (correlation_id, service_name) pair is first-seen.
LUA_RECORD_RESULT_AND_DECR_IF_FIRST_SEEN = """
local current = redis.call('get', KEYS[1])
if not current then
    -- First time seeing this job: set the expected count from the Docker Registry
    redis.call('set', KEYS[1], ARGV[1])
end

-- Keep both keys alive while results are arriving
redis.call('expire', KEYS[1], ARGV[2])

-- Record per-service status; HSET returns 1 only when the field is new
local is_new = redis.call('hset', KEYS[2], ARGV[3], ARGV[4])
redis.call('expire', KEYS[2], ARGV[2])

if is_new == 1 then
    -- First time seeing this service for the job: decrement and return new value
    return redis.call('decr', KEYS[1])
end

-- Duplicate delivery for the same service: do not decrement
return tonumber(redis.call('get', KEYS[1]))
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
        self._lua_script = self.redis.register_script(LUA_RECORD_RESULT_AND_DECR_IF_FIRST_SEEN)

    def handle_message(
        self,
        body: bytes,
        correlation_id: str | None,
        *,
        service_name: str | None = None,
        moderation_type: str | None = None,
        expected_workers: int | None = None,
    ) -> Optional[JobCompletedEvent]:
        if not correlation_id:
            LOGGER.error("Dropping result event with no correlation_id")
            return None
        if not service_name:
            LOGGER.error("Dropping result event with no x-service-name header; correlation_id=%s", correlation_id)
            return None

        try:
            raw_data = json.loads(body.decode("utf-8"))
            if isinstance(raw_data, dict):
                # service_name is authoritative from the AMQP header
                raw_data["service_name"] = service_name
            result = ResultEvent.model_validate(raw_data)
        except Exception as e:
            LOGGER.error("Failed to parse inbound event: %s", e)
            return None

        correlation_id = str(correlation_id) if correlation_id else None
        if not correlation_id:
            return None

        # Defensive: should always be set from the header
        if not result.service_name:
            LOGGER.error("Dropping result event with no service_name; correlation_id=%s", correlation_id)
            return None

        count_key = f"agg:{correlation_id}:count"
        data_key = f"agg:{correlation_id}:data"
        final_key = f"agg:{correlation_id}:final"

        # 1. Decide how many results we expect for this job.
        # By default we count all running moderators, but when jobs are routed by content type
        # (e.g., text vs image), we need a per-type count to avoid hanging forever.
        resolved_expected_workers = expected_workers
        if resolved_expected_workers is None:
            resolved_expected_workers = self.registry.count_for_type(moderation_type)
        if resolved_expected_workers < 1:
            LOGGER.warning(
                "Resolved expected_workers=%s (type=%s); forcing to 1; correlation_id=%s",
                resolved_expected_workers,
                moderation_type,
                correlation_id,
            )
            resolved_expected_workers = 1

        # 2. Atomic Update: init counter if missing, record per-service status,
        # and only decrement when the service is first-seen for this correlation_id.
        remaining = self._lua_script(
            keys=[count_key, data_key],
            args=[resolved_expected_workers, AGG_TTL_SECONDS, result.service_name, result.status],
        )

        LOGGER.info("Job %s: %s services remaining", correlation_id, remaining)

        # 4. Finalize if we hit zero (do NOT cleanup Redis state here; cleanup only after publish succeeds)
        if remaining == 0:
            cached = self.redis.get(final_key)
            if cached:
                try:
                    return JobCompletedEvent.model_validate_json(cached)
                except Exception:
                    LOGGER.warning("Ignoring invalid cached final event; correlation_id=%s", correlation_id)

            final_event = self._build_final_event(correlation_id, data_key)
            # Store a retryable copy for safety (TTL matches aggregation state).
            self.redis.set(final_key, final_event.model_dump_json(exclude_none=True))
            self.redis.expire(final_key, AGG_TTL_SECONDS)
            return final_event
        
        return None

    def cleanup(self, correlation_id: str) -> None:
        count_key = f"agg:{correlation_id}:count"
        data_key = f"agg:{correlation_id}:data"
        final_key = f"agg:{correlation_id}:final"
        self.redis.delete(data_key, count_key, final_key)

    def _build_final_event(self, correlation_id: str, data_key: str) -> JobCompletedEvent:
        all_results = self.redis.hgetall(data_key)

        # Logic: If any worker rejected, the whole post is rejected
        statuses = set(all_results.values())
        
        final_status = Status.APPROVED
        if Status.REJECTED in statuses:
            final_status = Status.REJECTED
        elif Status.FAILED in statuses:
            final_status = Status.FAILED

        return JobCompletedEvent(
            status=final_status,
            reason=f"Aggregated from {len(all_results)} workers."
        )
