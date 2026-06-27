FROM python:3.11-slim

ARG REQUIREMENTS_FILE=backend/requirements.txt
ARG APP_MODULE=app.main:app

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_URL=sqlite:////data/setu.db \
    SCHEMAS_DIR=/schemas \
    SETU_APP_MODULE=${APP_MODULE}

COPY ${REQUIREMENTS_FILE} requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --default-timeout=300 --retries 5 -r requirements.txt

COPY backend/app ./app
COPY schemas /schemas
COPY data /app/bundled-data

COPY backend/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh && mkdir -p /data

EXPOSE 8000

ENTRYPOINT ["/docker-entrypoint.sh"]