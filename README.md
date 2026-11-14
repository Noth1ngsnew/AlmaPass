# AlmaPass

A unified platform for aggregating city events in Almaty and rewarding visits with NFTs.

Stack: Django + PostgreSQL (backend), Angular (frontend), ERC-721 on a test network (NFT).

## Backend: запуск

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # впишите пароль своей PostgreSQL
createdb almapass               # или создайте базу через pgAdmin
python manage.py migrate
python manage.py setup_roles    # группы Moderators и Support для админки
python manage.py createsuperuser
python manage.py seed_demo      # демо-данные: категории, площадки, 18 событий
python manage.py runserver
```

Админ-панель: http://127.0.0.1:8000/admin/

Тесты: `python manage.py test`

## Frontend: запуск

Нужен Node.js 20 или новее. Бэкенд должен быть запущен.

```bash
cd frontend
npm install
npm start
```

Сайт: http://localhost:4200

## Check-in с телефона

QR-код ведёт на адрес сайта, поэтому телефон должен видеть ваш компьютер. Подключите оба к одной сети Wi-Fi и запустите серверы так:

```bash
python manage.py runserver 0.0.0.0:8000   # в backend
npm run start:lan                          # в frontend
```

Узнайте адрес компьютера (`ipconfig getifaddr en0` на Mac) и откройте сайт по нему, например `http://192.168.1.5:4200`. QR-код на странице организатора будет содержать этот же адрес.

Перед показом запустите `python manage.py seed_demo`: команда сдвигает событие «AlmaPass Demo Day» на текущее время, а отметиться можно только во время события.

## API

Авторизация: заголовок `Authorization: Bearer <access>`. Язык ответа: `?lang=ru` или заголовок `Accept-Language` (en, ru, kk).

| Метод и путь | Кто | Что делает |
|---|---|---|
| `POST /api/auth/register/` | все | Регистрация |
| `POST /api/auth/login/` | все | Вход, выдаёт `access` и `refresh` |
| `POST /api/auth/refresh/` | все | Обновление токена |
| `GET, PATCH /api/auth/me/` | вошедший | Профиль, кошелёк, язык |
| `GET /api/events/` | все | Каталог; фильтры `category`, `venue`, `organizer`, `date_from`, `date_to`, `free`, `mine` |
| `POST /api/events/` | организатор | Создать событие (уходит на модерацию) |
| `PATCH, DELETE /api/events/{id}/` | владелец, админ | Изменить или удалить |
| `POST /api/events/{id}/moderate/` | админ | Опубликовать или отклонить |
| `POST, DELETE /api/events/{id}/favorite/` | вошедший | Добавить в избранное или убрать |
| `GET /api/search/?q=текст` | все | Поиск по событиям, площадкам и организаторам |
| `GET /api/favorites/` | вошедший | Моё избранное |
| `POST /api/checkin/` | вошедший | Отметка посещения по коду из QR |
| `GET /api/visits/` | вошедший | Мои посещения и статус NFT |
| `GET /api/events/{id}/checkin-code/` | владелец, админ | Код для QR и число отметившихся |
| `POST /api/organizers/apply/` | вошедший | Стать организатором |
| `GET /api/categories/`, `/api/venues/`, `/api/organizers/` | все | Справочники |

## Структура

Бэкенд (`backend/`):

| Приложение | Модели |
|---|---|
| `accounts` | User (роль, кошелёк, язык) |
| `events` | Category, Venue, Organizer, Event, Favorite |
| `rewards` | Visit (check-in), NFTReward |

Фронтенд (`frontend/src/app/`):

| Папка | Что внутри |
|---|---|
| `core/` | Модели, запросы к API, авторизация, переводы |
| `components/` | Карточка события, кнопка избранного |
| `pages/` | Каталог, событие, поиск, вход и регистрация, избранное, профиль, сканер, отметка, QR-код организатора, посещения |
