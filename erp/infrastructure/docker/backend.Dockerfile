# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps for psycopg2 build + healthcheck tooling.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements/ requirements/
ARG REQ=dev
RUN pip install -r requirements/${REQ}.txt

COPY backend/ /app/
COPY scripts/entrypoint.sh /usr/local/bin/entrypoint.sh
# 755 (not merely +x): the container later switches to the non-root appuser,
# who must be able to READ the script, not only execute it. A 7x1 file would
# fail with "Permission denied" at container start under that user.
RUN chmod 755 /usr/local/bin/entrypoint.sh

# Non-root runtime user.
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8000
ENTRYPOINT ["entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
