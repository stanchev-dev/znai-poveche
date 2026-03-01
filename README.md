# Знай Повече

**Знай Повече** е образователна уеб платформа, разработена с Django, която обединява:

- дискусии и учебни въпроси
- коментари и гласуване
- точки / ангажираност
- маркетплейс за образователни обяви
- докладване и модерация

## Технологии

- Django
- Django REST Framework
- Bootstrap 5
- HTML, CSS, JavaScript
- SQLite (локално)
- PostgreSQL (production)
- Cloudinary (media)
- WhiteNoise (static)
- Gunicorn
- Railway

## Локално стартиране

1. Създай виртуална среда:

    python -m venv .venv

2. Активирай я:

   **Windows (PowerShell):**

    .venv\Scripts\Activate.ps1

   **Linux / macOS:**

    source .venv/bin/activate

3. Инсталирай зависимостите:

    pip install -r requirements.txt

4. Приложи миграциите:

    python manage.py migrate

5. Стартирай проекта:

    python manage.py runserver

## Seed демо данни

За зареждане на примерни данни:

    python manage.py seed

Може да използвате следните акаунти за тестване:

- Администраторски - `admin / admin12345`
- Потребителски - `demo / demo12345`

За пълно локално презареждане на seed данните:

    python manage.py seed --wipe

## Тестове

Стартиране на тестовете:

    python manage.py test

## Статични файлове

Събиране на static файлове:

    python manage.py collectstatic --noinput

## Production бележки

В production среда:

- `DEBUG=False`
- `ALLOWED_HOSTS` се подава чрез environment variable като CSV  
  Пример: `example.com,www.example.com`

Проектът е конфигуриран за:

- PostgreSQL
- Cloudinary
- WhiteNoise
- Gunicorn
- Railway

## Production версия

Проектът е достъпен на:

**https://znaipoveche.eu**

`www` версията пренасочва към non-www домейна.

## Полезни команди

    python manage.py runserver
    python manage.py migrate
    python manage.py test
    python manage.py seed
    python manage.py seed --wipe
    python manage.py collectstatic --noinput
