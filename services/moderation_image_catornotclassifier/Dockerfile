FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

# Enable bytecode compilation for faster app startup
ENV UV_COMPILE_BYTECODE=1

# 1. Copy ONLY the dependency files first
COPY pyproject.toml uv.lock ./

# 2. Install dependencies (this layer is cached unless dependencies change)
RUN uv sync --frozen --no-install-project --no-dev

# 3. Copy the rest of your application code
COPY . .

# 4. Final sync to install the project itself (very fast)
RUN uv sync --frozen --no-dev

CMD ["uv", "run", "faststream", "run", "app.serve:app"]
