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

## Best Practices

- Use multi-stage builds to reduce image size
- Pin Python version (`python:3.12-slim`)
- Add HEALTHCHECK for container orchestration
- Use `.dockerignore` to exclude unnecessary files
- Don't run as root

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
