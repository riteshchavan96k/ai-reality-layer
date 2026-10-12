# Step 231: isolated pilot runtime. Not an internet-facing deployment by itself.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    ARL_RUNTIME_MODE=pilot

WORKDIR /srv
COPY backend/requirements.txt /srv/backend/requirements.txt
RUN python -m pip install --no-cache-dir -r /srv/backend/requirements.txt \
    && groupadd --system --gid 10001 arl \
    && useradd --system --uid 10001 --gid 10001 --no-create-home arl

COPY backend/app /srv/backend/app
USER 10001:10001
EXPOSE 8080

# Refuse to launch if the token or original-source allowlist is invalid.
# Ingress must provide TLS termination, rate limits, body limits and logging.
CMD ["sh", "-c", "python -m backend.app.api.pilot_auth && exec python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8080 --workers 1 --no-access-log"]
