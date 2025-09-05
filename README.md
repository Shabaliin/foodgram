# Foodgram

Кулинарный проект: сервис рецептов с подписками, избранным, корзиной покупок и короткими ссылками.

## Ссылка на проект

- Прод: http://84.201.167.223

## Автор

- ФИО: Шабалин Алексей Андреевич
- GitHub: https://github.com/Shabaliin

## Технологический стек

- Backend: Python 3.11, Django 4, Django REST Framework, Djoser, drf-spectacular, django-filter, Pillow
- DB: PostgreSQL
- Web: Nginx
- WSGI: Gunicorn
- Контейнеризация: Docker, Docker Compose
- CI/CD: GitHub Actions

## CI/CD

- Сборка и пуш образа backend в реестр (Docker Hub/GHCR) по push в main
- Автодеплой на сервер через SSH: подготовка окружения (.env), `docker compose up -d --build`

## Локальный запуск с Docker

1) Клонирование репозитория
```bash
git clone https://github.com/Shabaliin/foodgram.git
cd foodgram
```

2) Перейти в папку с docker-compose.yml
```bash
cd infra
```

3) Подсказка по .env (создайте файл .env рядом с docker-compose.yml)
```env
# БД
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram
POSTGRES_PASSWORD=foodgram
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Django
DJANGO_ALLOWED_HOSTS=*
DJANGO_DEBUG=1
```

4) Поднять контейнеры
```bash
docker compose up -d --build
```

5) Подготовить базу данных и данные (если entrypoint не делает это автоматически)
```bash
docker compose exec backend python manage.py migrate
# (опционально) суперпользователь
docker compose exec backend python manage.py createsuperuser
# импорт ингредиентов и демо-данных
docker compose exec backend python manage.py load_ingredients --from /app/data/ingredients.csv
docker compose exec backend python manage.py seed_demo
# собрать статику
docker compose exec backend python manage.py collectstatic --noinput
```

6) Полезные ссылки
- Frontend: http://localhost/
- API Redoc: http://localhost/api/schema/redoc/
- Admin: http://localhost/admin/

## Локальный запуск без Docker

1) Клонирование репозитория и переход
```bash
git clone https://github.com/Shabaliin/foodgram.git
cd foodgram/backend
```

2) Виртуальное окружение
- Windows PowerShell
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
- macOS/Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3) Установка зависимостей
```bash
pip install -r requirements.txt
```

4) Переменные окружения
- Создайте файл `.env` или экспортируйте переменные в сессию:
```env
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram
POSTGRES_PASSWORD=foodgram
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
DJANGO_DEBUG=1
```

5) Миграции, суперпользователь, данные, статика
```bash
python manage.py migrate
python manage.py createsuperuser
# импорт ингредиентов (вариант 1 — management command)
python manage.py load_ingredients --from ./data/ingredients.csv
# (вариант 2 — json фикстура если подходит формату)
python manage.py loaddata ../data/ingredients.json
python manage.py collectstatic --noinput
```

6) Запуск сервера (без Docker)
```bash
python manage.py runserver 0.0.0.0:8000
```

7) Документация API (локально)
- http://127.0.0.1:8000/api/schema/redoc/

## Структура API (вкратце)

- Авторизация: Djoser (email + токен)
- Пользователи: профиль, подписки, аватар
- Рецепты: CRUD, теги, ингредиенты, избранное, корзина, выгрузка покупок, короткие ссылки

## Полезное

- Статик/медиа обслуживаются Nginx
- Короткие ссылки: префикс /s/
- Точки входа документации: `/api/schema/`, `/api/schema/redoc/`
