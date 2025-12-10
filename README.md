# SafuForum – Event-Driven Moderation Stack (Local Dev)

This repo hosts the local, event-driven microservices stack for SafuForum. It includes moderation composites (text/image), content/user services, and supporting infra (RabbitMQ, Redis, Postgres, SeaweedFS S3 gateway) orchestrated via Docker Compose. The `ai/` folder holds ML training artifacts/models (.pth) and is not part of the runtime services.

## Prerequisites
- Docker
- Optional: `awscli` or `mc` for S3-compatible checks

## Run the stack (local)
```bash
docker compose up -d
```
- Services come up on the `safuforum-net` network with ports mapped to localhost (see below). If a port is taken, edit the `ports` mapping in `docker-compose.yml`.

## Host Ports (Local Development)
| Service                | Port(s)                      |
|------------------------|------------------------------|
| RabbitMQ               | 5672 (AMQP), 15672 (Mgmt UI) |
| SeaweedFS S3 Gateway   | 8333 (S3 API)                |
| SeaweedFS Master UI    | 9333                         |
| SeaweedFS Volume Debug | 8080                         |
| SeaweedFS Filer Web UI | 8888                         |
| Redis                  | 6379                         |
| Postgres               | 5432                         |

## Key services & ports
- RabbitMQ
  - AMQP: `localhost:5672`
  - Management UI: `http://localhost:15672` (user/pass: guest/guest)

- SeaweedFS (S3-compatible storage)
  - S3 API: `http://localhost:8333` (`S3_ENDPOINT`)
  - Master UI/API: `http://localhost:9333`
  - Volume server (debug): `http://localhost:8080`
  - Change ports by editing `docker-compose.yml` mappings.
  - Example bucket list: `AWS_ACCESS_KEY_ID=dev AWS_SECRET_ACCESS_KEY=dev aws s3api --endpoint-url http://localhost:8333 list-buckets`

- Redis: `localhost:6379`
- Postgres: `localhost:5432` (DBs: `users_db`, `content_db`, `moderation_db`, `assignment_db`)

## Project layout
- `ai/` – ML training artifacts/models (.pth)
- `services/` – app services (content, user, moderation-text, moderation-image, assignment, etc.)
- `docker-compose.yml` – local orchestration
- `postgres-init.sql` – creates domain databases on startup
- `content-moderation-implementation.md` / `Implementation.md` – design docs

## Helpful commands
- Logs: `docker compose logs -f <service>`
- RabbitMQ queues: `docker compose exec rabbitmq rabbitmqctl list_queues`
- Stop stack: `docker compose down` (add `-v` to drop volumes for a clean reset)

## Notes
- All storage uses the S3-compatible endpoint; swapping storage backends is an endpoint/creds change.
- Observability is intentionally minimal for now; focus is on event wiring and moderation flow.***
