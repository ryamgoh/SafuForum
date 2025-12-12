# Moderation Orchestrator Event Formats

Envelope fields (all events):
- `message_id`: unique UUID per message.
- `type`: namespaced + versioned event type.
- `correlation_id`: job identifier shared across all task/job events.
- `service_id`: publisher identifier.
- `timestamp`: ISO 8601 UTC string.
- `payload`: event-specific data.

## Task Requested (`Moderation.Task.Requested.v1`)
```json
{
  "message_id": "uuid",
  "type": "Moderation.Task.Requested.v1",
  "correlation_id": "job-uuid",
  "service_id": "orchestrator",
  "timestamp": "2024-06-01T12:00:00Z",
  "payload": {
    "job_id": "job-uuid",
    "task": { "service_id": "Deepfake_V1" },
    "content": { "text": "...", "image_uri": "s3://..." }
  }
}
```

## Task Completed (`Moderation.Task.Completed.v1`)
```json
{
  "message_id": "uuid",
  "type": "Moderation.Task.Completed.v1",
  "correlation_id": "job-uuid",
  "service_id": "Deepfake_V1",
  "timestamp": "2024-06-01T12:00:01Z",
  "payload": {
    "job_id": "job-uuid",
    "service_id": "Deepfake_V1",
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
  "correlation_id": "job-uuid",
  "service_id": "orchestrator",
  "timestamp": "2024-06-01T12:00:02Z",
  "payload": {
    "job_id": "job-uuid",
    "final_verdict": "allow|block|review|error",
    "final_score": 0.75,
    "timed_out": false,
    "task_count": 3
  }
}
```

Notes:
- Keep envelope fields consistent across all events; domain data lives in `payload`.
- Routing keys/topics can mirror `type` (e.g., `moderation.task.requested`, `moderation.task.completed`, `moderation.job.completed`).
- Include `service_id` in both envelope and payload where it is part of the domain (task completion).***
