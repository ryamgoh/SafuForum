FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

COPY . /app

RUN uv sync

CMD ["uv", "run", "python", "-m", "moderation_text_toxicornotclassifier"]
