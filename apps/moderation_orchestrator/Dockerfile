FROM python:3.13-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt ./requirements.txt
COPY pyproject.toml ./pyproject.toml

# Use uv for faster installs; fallback to pip if desired.
RUN pip install --no-cache-dir uv \
    && uv pip install --system --no-cache-dir -r requirements.txt

COPY . .

# Adjust the module/host/port as needed. The consumer starts on app startup.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
