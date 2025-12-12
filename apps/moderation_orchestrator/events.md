# Moderation Orchestrator Event Formats

Envelope fields (all events):
- `message_id`: unique UUID per message.
- `type`: namespaced + versioned event type.
- `correlation_id`: correlating identifier shared across all task/job events.
- `service_id`: publisher identifier.
- `timestamp`: ISO 8601 UTC string.
- `payload`: event-specific data.

## Task Requested (`Moderation.Task.Requested.v1`)
```json
{
  "message_id": "uuid",
  "type": "Moderation.Task.Requested.v1",
  "correlation_id": "correlating-uuid",
  "service_id": "orchestrator",
  "timestamp": "2024-06-01T12:00:00Z",
  "payload": {
    "correlating_id": "correlating-uuid",
    "task": { "event_name": "Deepfake_V1" },
    "content": { "text": "...", "image_uri": "s3://..." }
  }
}
```

## Task Completed (`Moderation.Task.Completed.v1`)
```json
{
  "message_id": "uuid",
  "type": "Moderation.Task.Completed.v1",
  "correlation_id": "correlating-uuid",
  "service_id": "Deepfake_V1",
  "timestamp": "2024-06-01T12:00:01Z",
  "payload": {
    "correlating_id": "correlating-uuid",
    "event_name": "Deepfake_V1",
    "verdict": "allow|block|review|error",
    "score": 0.92,
    "details": { "reason": "deepfake detected" }
  }
}
```

## Job Completed (`Moderation.Job.Completed.v1`)
```json
{
  "message_id": "uuid",
  "type": "Moderation.Job.Completed.v1",
  "correlation_id": "correlating-uuid",
  "service_id": "orchestrator",
  "timestamp": "2024-06-01T12:00:02Z",
  "payload": {
    "correlating_id": "correlating-uuid",
    "final_verdict": "allow|block|review|error",
    "timed_out": false
  }
}
```

Notes:
- Keep envelope fields consistent across all events; domain data lives in `payload`.
- Routing keys/topics can mirror `type` (e.g., `moderation.task.requested`, `moderation.task.completed`, `moderation.job.completed`).
- Include `service_id` in both envelope and payload where it is part of the domain (task completion).***
