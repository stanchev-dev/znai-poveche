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
- Cloudinary (media качване/съхранение в production)
- WhiteNoise (сервиране на static файлове в production)
- Gunicorn (WSGI сървър за Django процеса)
- Railway (хостинг/деплой платформа)

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

- PostgreSQL – основна production база данни.
- Cloudinary – съхранение и сервиране на media (снимки към профили, постове, обяви).
- WhiteNoise – директно сервиране на static файлове (CSS/JS/икони) от Django приложението.
- Gunicorn – процесен HTTP/WSGI сървър, който стартира Django app-а в production.
- Railway – инфраструктура за build, deploy, env variables, домейн и runtime логове.

## Кратко: „За какво са ми Cloudinary, WhiteNoise и Gunicorn?“

- **Cloudinary** ти трябва за **media файловете**, качвани от потребителите (например изображения).
  Ако нямаш Cloudinary (или алтернативно object storage), тези файлове няма да са устойчиво достъпни в production.
- **WhiteNoise** ти трябва за **static файловете** (CSS/JS), за да се сервират коректно след `collectstatic`,
  без отделен Nginx само за static.
- **Gunicorn** ти трябва, защото `runserver` е dev сървър. В production Django трябва да върви зад стабилен WSGI сървър.

Ако правиш само локална разработка, можеш временно да минеш без тях:
- media локално в `MEDIA_ROOT`;
- static през `runserver`;
- стартиране с `python manage.py runserver`.

## Деплой (Railway) – пълен walkthrough

### 1) Подготовка на услугата

1. Създай нов проект в Railway и свържи GitHub репото.
2. Добави PostgreSQL plugin към проекта.
3. Увери се, че build използва `requirements.txt` и Python runtime.
4. Задай Start Command:

    gunicorn config.wsgi:application --bind 0.0.0.0:$PORT

### 2) Задължителни environment променливи

- `SECRET_KEY` – произволен дълъг secret.
- `DEBUG=False`
- `DATABASE_URL` – идва от Railway PostgreSQL.
- `ALLOWED_HOSTS` – CSV, напр. `znaipoveche.eu,www.znaipoveche.eu`.
- `CSRF_TRUSTED_ORIGINS` – CSV с пълни origin-и, напр. `https://znaipoveche.eu,https://www.znaipoveche.eu`.
- `CANONICAL_HOST` – каноничен домейн без схема, напр. `znaipoveche.eu`.
- `CLOUDINARY_URL` – Cloudinary connection string за media файловете.

> Логика на `DEBUG`: ако не е зададен `DEBUG`, приложението автоматично минава в `DEBUG=False`, когато има `DATABASE_URL`.

### 3) Release процес (след deploy)

След всеки deploy изпълни:

    python manage.py migrate
    python manage.py collectstatic --noinput

По желание за демо среда:

    python manage.py seed

### 4) Домейн и HTTPS

- Насочи домейна към Railway услугата (A/CNAME според инструкциите на Railway).
- Активирай TLS сертификат през Railway.
- Настрой `CANONICAL_HOST=znaipoveche.eu`, за да пренасочва `www` към non-www.

### 5) Кои портове се ползват

- **Локално (Django dev server):** `8000` по подразбиране (`python manage.py runserver`).
- **Production (Railway):** приложението слуша на `PORT`, който Railway подава като env variable.
  Затова start command е `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`.
- **PostgreSQL:** стандартно `5432`, но в Railway това е вътрешна managed услуга и се достъпва чрез `DATABASE_URL`
  (не отваряш ръчно порт към интернет за приложението).
- **HTTPS за крайни потребители:** трафикът е на `443` (TLS), а `80` се ползва за HTTP/redirect според настройките на платформата.

## Входящи заявки (Inbound request flow)

1. Клиент (браузър) изпраща HTTP(S) заявка към Railway.
2. Railway reverse proxy подава заявката към Django/Gunicorn контейнера.
3. В Django първо минава `CanonicalDomainRedirectMiddleware`:
   - при `GET/HEAD` и `DEBUG=False` прави 301 redirect от `www.` към каноничния host;
   - за `POST/PUT/PATCH/DELETE` не пренасочва (за да не се чупят форми/API заявки).
4. Заявката се рутира от `config/urls.py`:
   - Web страници: `common`, `discussions`, `marketplace`, `accounts`;
   - API: всички endpoints под `/api/...`.
5. Отговорът се връща обратно през Railway към клиента.

### Основни входящи API групи

- `GET /api/health/` – health check.
- Discussions API:
  - `GET /api/subjects/`
  - `GET|POST /api/posts/`
  - `GET /api/posts/<id>/`
  - `POST /api/posts/<id>/vote/`
  - `GET|POST /api/posts/<id>/comments/`
  - `POST /api/comments/<id>/vote/`
  - `DELETE /api/comments/<id>/`
- Marketplace API:
  - `GET|POST /api/listings/`
  - `GET /api/listings/<id>/`
  - `POST /api/listings/<id>/contact/`
  - `POST /api/listings/<id>/vip/`
- Moderation API:
  - `POST /api/reports/`
  - `GET /api/admin/reports/`
  - `POST /api/admin/actions/`

## Изходящи заявки (Outbound request flow)

### От браузъра към backend

- Frontend JS ползва `fetch` през helper (`static/js/api.js`), който:
  - праща `credentials: same-origin` (cookie сесия);
  - добавя `X-CSRFToken` за mutating заявки (`POST/PUT/PATCH/DELETE`);
  - добавя `Content-Type: application/json`, когато тялото не е `FormData`.

### От backend към външни услуги

- PostgreSQL: Django ORM изпраща SQL заявки през `DATABASE_URL`.
- Cloudinary: media upload/достъп минава през `django-cloudinary-storage`, когато има `CLOUDINARY_URL`.
- Static assets: в production WhiteNoise обслужва статичните файлове директно от приложението.

## Чеклист за дебъг на deploy

1. `500` грешка след deploy:
   - провери `SECRET_KEY`, `DATABASE_URL`, `CLOUDINARY_URL`.
2. `DisallowedHost`:
   - добави домейна в `ALLOWED_HOSTS`.
3. CSRF грешки:
   - добави origin в `CSRF_TRUSTED_ORIGINS`.
4. Липсващи CSS/JS:
   - пусни `collectstatic --noinput`.
5. Проблем с www/non-www:
   - провери `CANONICAL_HOST` и DNS записа за `www`.

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
