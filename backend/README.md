# Foodgram Backend

## Quickstart (Docker)

- docker compose -f infra/docker-compose.yml up -d --build
- docker exec -it foodgram-back python manage.py migrate
- docker exec -it foodgram-back python manage.py createsuperuser
- docker exec -it foodgram-back python manage.py load_ingredients --from /app/../data/ingredients.csv

API served at /api, shortlinks at /s.

## Local env

- python -m venv .venv && .venv/Scripts/activate (Windows)
- pip install -r backend/requirements.txt
- python backend/manage.py migrate
- python backend/manage.py runserver 0.0.0.0:8000

