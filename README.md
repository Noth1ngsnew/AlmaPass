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

Тесты: `python manage.py test`. Тесты выдачи NFT запускаются, если установлен `requirements-dev.txt` (локальная сеть в памяти).

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

## NFT: настройка (один раз)

NFT выдаются в тестовой сети Polygon Amoy: это бесплатно, настоящие деньги не нужны. Без настройки сайт работает как обычно, а NFT остаются в статусе «Ещё не получен».

1. Создайте серверный кошелёк, с которого сервер будет выдавать токены:
   ```bash
   python manage.py create_nft_wallet
   ```
   Команда покажет адрес и строку `NFT_PRIVATE_KEY=...`. Строку впишите в `backend/.env`.
2. Получите на показанный адрес тестовые монеты POL: https://faucet.polygon.technology/ (сеть Polygon Amoy).
3. Опубликуйте смарт-контракт:
   ```bash
   python manage.py deploy_nft_contract
   ```
   Команда покажет строку `NFT_CONTRACT_ADDRESS=...`. Её тоже впишите в `backend/.env`.
4. Перезапустите сервер и проверьте:
   ```bash
   python manage.py nft_status
   ```

Пользователю нужен только адрес кошелька в профиле (кнопка «Подключить MetaMask»). После check-in сервер сам выдаёт NFT, статус виден на странице «Мои NFT». Команда `python manage.py nft_status --retry` повторяет незавершённые выдачи.

Исходник контракта лежит в `contracts/AlmaPassNFT.sol`, скомпилированная версия — в `backend/rewards/contract/AlmaPassNFT.json`. Пересобрать: `cd contracts && npm install && npm run compile`.

## Уровни NFT и скидки

Каждый выданный NFT повышает уровень пользователя. Уровни хранятся в таблице `rewards_loyaltylevel` и меняются в админ-панели:

| Уровень | NFT | Скидка |
|---|---|---|
| Bronze | 1 | — |
| Silver | 3 | 10% |
| Gold | 5 | 15% |
| Platinum | 10 | 20% |

На платном событии (если организатор не выключил «Скидку для владельцев NFT») пользователь с уровнем Silver и выше получает одноразовый код вида `ALMA-XXXX-XXXX`. Организатор вводит код в своём кабинете («Проверка кода скидки») — код помечается использованным. Процент фиксируется в момент выдачи.

Подготовка к показу: чтобы у пользователя сразу был уровень Silver, выдайте ему 3 настоящих NFT (нужен настроенный NFT и кошелёк в профиле):

```bash
python manage.py give_demo_nfts <логин> --count 3
```

## Показ базы данных

Все действия на сайте сразу записываются в PostgreSQL. В `docs/database-demo.sql` лежат готовые запросы для DataGrip: пользователи, избранное, посещения и NFT, события и модерация, уровни, коды скидок, поиск. Сделайте действие на сайте и выполните соответствующий запрос — появится новая строка.

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
| `GET /api/search/?q=текст` | все | Поиск по названиям событий, площадок и организаторов |
| `GET /api/favorites/` | вошедший | Моё избранное |
| `POST /api/checkin/` | вошедший | Отметка посещения по коду из QR |
| `GET /api/visits/` | вошедший | Мои посещения и статус NFT |
| `GET /api/events/{id}/checkin-code/` | владелец, админ | Код для QR и число отметившихся |
| `POST /api/visits/{id}/claim/` | вошедший | Получить NFT за посещение или повторить выдачу |
| `GET /api/nft/metadata/{id}/` | все | Метаданные токена (на них ссылается `tokenURI`) |
| `GET /api/loyalty/` | все | Уровни NFT и прогресс текущего пользователя |
| `POST /api/events/{id}/discount/` | вошедший | Получить код скидки на платное событие по своему уровню |
| `GET /api/discounts/` | вошедший | Мои коды скидок |
| `POST /api/discounts/redeem/` | организатор, админ | Погасить код скидки на своём событии |
| `POST /api/organizers/apply/` | вошедший | Стать организатором |
| `GET, PATCH /api/organizers/me/` | организатор | Свой профиль организатора |
| `GET /api/categories/`, `/api/venues/`, `/api/organizers/` | все | Справочники |

## Структура

Бэкенд (`backend/`):

| Приложение | Модели |
|---|---|
| `accounts` | User (роль, кошелёк, язык) |
| `events` | Category, Venue, Organizer, Event, Favorite |
| `rewards` | Visit (check-in), NFTReward, LoyaltyLevel, DiscountCode |

Фронтенд (`frontend/src/app/`):

| Папка | Что внутри |
|---|---|
| `core/` | Модели, запросы к API, авторизация, переводы |
| `components/` | Карточка события, кнопка избранного |
| `pages/` | Каталог, событие, поиск, вход и регистрация, избранное, профиль, сканер, отметка, QR-код организатора, коллекция NFT, кабинет организатора, форма события |

## Диаграммы

Диаграммы для презентации лежат в `docs/`: ER-диаграмма (`er-diagram.png`) и диаграмма вариантов использования (`use-case-diagram.png`). Они построены по моделям и ролям из кода.
