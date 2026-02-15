# Znai Poveche

## Локално стартиране
1. `python -m venv .venv && source .venv/bin/activate`
2. `pip install -r requirements.txt`
3. `python manage.py migrate`
4. `python manage.py runserver`

## Seed демо данни
- `python manage.py seed`

Създава:
- `admin / admin12345`
- `demo / demo12345`

## Тестове
- `python manage.py test`

## Статични файлове
- `python manage.py collectstatic --noinput`

## Production очаквания
- `DEBUG=False`
- `ALLOWED_HOSTS` се подава чрез env променлива (CSV, напр. `example.com,www.example.com`).
