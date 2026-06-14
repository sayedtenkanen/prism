---
name: docker
description: Dockerfile patterns, multi-stage builds, and containerization. Use when user mentions "docker", "dockerfile", "container", "image". Triggers on Docker questions.
---

# Docker Conventions

## Prism Dockerfile

```dockerfile
# Multi-stage build
FROM python:3.12-slim AS builder
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY app/ app/
HEALTHCHECK --interval=30s CMD python -c "import httpx; httpx.get('http://localhost:8000/health')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Docker Compose

```yaml
# docker-compose.yml
version: "3.8"
services:
  prism:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SCM_GITHUB_TOKEN=${SCM_GITHUB_TOKEN}
      - LLM_API_KEY=${LLM_API_KEY}
    volumes:
      - ./app:/app/app
    healthcheck:
      test: ["CMD", "python", "-c", "import httpx; httpx.get('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Best Practices

- Use multi-stage builds to reduce image size
- Pin Python version (`python:3.12-slim`)
- Add HEALTHCHECK for container orchestration
- Use `.dockerignore` to exclude unnecessary files
- Don't run as root
- Use docker-compose for local development

## .dockerignore

```
.git
.github
.pytest_cache
__pycache__
*.pyc
venv
.env
.opencode
tests
```

## Checklist

Before committing Dockerfile:

```bash
docker build -t prism .
docker run -p 8000:8000 prism
curl http://localhost:8000/health
```

## Local Development

```bash
# Build and run with docker-compose
docker-compose up --build

# Run in background
docker-compose up -d

# Stop
docker-compose down
```
