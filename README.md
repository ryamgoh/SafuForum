# SafuForum

Full-stack forum app for local development: Next.js frontend + Spring Boot backend + Postgres + RabbitMQ, orchestrated with Docker Compose. The repo also includes a SeaweedFS deployment (S3-compatible) for local object storage experiments.

## Tech stack
- Frontend: Next.js + Tailwind CSS
- Backend: Spring Boot (REST) + Spring Security (Google OAuth2) + JWT + Flyway
- Infra (docker-compose): Postgres, RabbitMQ, SeaweedFS (master/volume/filer/s3)

## Quickstart (Docker)
1) Configure backend env vars in `backend/.env`:
```bash
# Database (only required if running backend outside Docker)
DB_USERNAME=postgres
DB_PASSWORD=postgres

# Google OAuth2
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...

# JWT
JWT_SECRET=...
```
(`backend/.env` is gitignored; don’t commit real secrets.)

2) Start the stack:
```bash
docker compose up -d --build
```

3) Open:
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8081`
- Swagger UI: `http://localhost:8081/swagger-ui/index.html`
- RabbitMQ UI: `http://localhost:15672` (guest/guest)

Stop everything:
```bash
docker compose down
```
(Add `-v` to remove volumes and reset the DB.)

## Host ports (local dev)
| Service | Port(s) |
|---|---|
| Frontend (Next.js) | 3000 |
| Backend (Spring Boot) | 8081 |
| Postgres | 5432 |
| RabbitMQ | 5672 (AMQP), 15672 (UI) |
| SeaweedFS master | 9333, 19333 |
| SeaweedFS volume (debug) | 8080 |
| SeaweedFS filer | 8888, 18888 |
| SeaweedFS S3 gateway | 8333 |

If a port is already taken, update `docker-compose.yml`.

## Useful commands
- Tail logs: `docker compose logs -f backend` (or `frontend`, `postgres`, `rabbitmq`)
- Rebuild containers: `docker compose up -d --build`
- Reset DB and volumes: `docker compose down -v`
- List RabbitMQ queues: `docker compose exec rabbitmq rabbitmqctl list_queues`

## Local development (run app code on host)
Bring up infra only:
```bash
docker compose up -d postgres rabbitmq
```

Run the backend:
```bash
cd backend
./gradlew bootRun
```
- If you want to use the Postgres DB created by Docker Compose, set `SPRING_DATASOURCE_URL=jdbc:postgresql://localhost:5432/safuforum`.
- If you want image uploads to use the SeaweedFS container, set `SEAWEEDFS_S3_ENDPOINT=http://localhost:8333` (the in-Docker default is `http://seaweed-s3:8333`).

Run the frontend:
```bash
cd frontend
npm ci
npm run dev
```
- Recommended: set `NEXT_PUBLIC_API_URL=http://localhost:8081` (for example in `frontend/.env.local`).
## Authentication (Google OAuth2)
- Login entrypoint: `http://localhost:8081/oauth2/authorization/google`
- Google Console redirect URI: `http://localhost:8081/login/oauth2/code/google`
- After login, the backend redirects to `http://localhost:3000/auth/callback` with `accessToken` and `refreshToken` query params.

## SeaweedFS (S3-compatible)
- S3 endpoint (from host): `http://localhost:8333`
- S3 endpoint (from backend container): `http://seaweed-s3:8333` (default; override with `SEAWEEDFS_S3_ENDPOINT`)
- Filer UI: `http://localhost:8888`
- Credentials (from `s3_identity.json`): access key `dev`, secret key `dev`
- Default bucket (backend): `safu-forum-images` (auto-created on first upload)
- Example (awscli):
  - `AWS_ACCESS_KEY_ID=dev AWS_SECRET_ACCESS_KEY=dev aws s3api --endpoint-url http://localhost:8333 list-buckets`

## Repo layout
- `services/frontend/` – Next.js app
- `services/backend/` – Spring Boot app (Flyway migrations in `src/main/resources/db/migration`)
- `services/backend/schema.dbml` – database diagram (derived from Flyway migrations)
- `docker-compose.yml` – local stack orchestration
- `ai/` – ML training artifacts/models (not used by the runtime app)
- `apps/` – experiments/prototypes
