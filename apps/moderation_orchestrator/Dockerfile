FROM ghcr.io/astral-sh/uv:0.9.17-python3.13-bookworm-slim

WORKDIR /app

# Copy just this service into the image (keeps the build context small)
COPY ./ ./

RUN uv sync --frozen

ENV PATH="/app/.venv/bin:${PATH}"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
