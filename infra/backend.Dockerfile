FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential \
	libpq-dev \
	&& rm -rf /var/lib/apt/lists/*

COPY ../backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ../backend /app

RUN chmod +x /app/entrypoint.sh

ENV DJANGO_SETTINGS_MODULE=foodgram_backend.settings

ENTRYPOINT ["/app/entrypoint.sh"]

