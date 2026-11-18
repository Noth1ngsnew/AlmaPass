-- AlmaPass: запросы для показа процессов в базе данных (DataGrip / pgAdmin)
--
-- Как показывать: сделайте действие на сайте, затем выполните соответствующий запрос
-- (в DataGrip: курсор на запросе → Ctrl+Enter / Cmd+Enter). Новая строка появится сверху.
-- База: almapass. Названия таблиц: <приложение>_<модель>, например events_favorite.


-- 0. Сколько строк в каждой таблице — обзор всей базы
SELECT 'accounts_user' AS table_name, count(*) AS rows FROM accounts_user
UNION ALL SELECT 'events_category', count(*) FROM events_category
UNION ALL SELECT 'events_venue', count(*) FROM events_venue
UNION ALL SELECT 'events_organizer', count(*) FROM events_organizer
UNION ALL SELECT 'events_event', count(*) FROM events_event
UNION ALL SELECT 'events_favorite', count(*) FROM events_favorite
UNION ALL SELECT 'rewards_visit', count(*) FROM rewards_visit
UNION ALL SELECT 'rewards_nftreward', count(*) FROM rewards_nftreward
UNION ALL SELECT 'rewards_loyaltylevel', count(*) FROM rewards_loyaltylevel
UNION ALL SELECT 'rewards_discountcode', count(*) FROM rewards_discountcode;


-- 1. Регистрация и профиль: новые пользователи (сайт: «Регистрация», «Профиль»)
SELECT id, username, email, role, wallet_address, language, date_joined
FROM accounts_user
ORDER BY date_joined DESC
LIMIT 10;


-- 2. Избранное: кто какое событие сохранил (сайт: сердечко на событии)
-- Если убрать сердечко, строка исчезнет
SELECT f.id, u.username, e.title_en AS event, f.created_at
FROM events_favorite f
JOIN accounts_user u ON u.id = f.user_id
JOIN events_event e ON e.id = f.event_id
ORDER BY f.created_at DESC;


-- 3. Check-in по QR и NFT: посещения и статус токена (сайт: «Скан QR», «Мои NFT»)
-- status: pending → minting → minted (или failed)
SELECT v.id AS visit_id, u.username, e.title_en AS event, v.checked_in_at,
       n.status AS nft_status, n.token_id, n.tx_hash, n.wallet_address
FROM rewards_visit v
JOIN accounts_user u ON u.id = v.user_id
JOIN events_event e ON e.id = v.event_id
LEFT JOIN rewards_nftreward n ON n.visit_id = v.id
ORDER BY v.checked_in_at DESC;


-- 4. События организаторов: статус и число отметок (сайт: «Организатору»)
SELECT e.id, e.title_en AS event, o.name AS organizer, e.status, e.price, e.nft_discount,
       e.start_at, count(v.id) AS check_ins
FROM events_event e
JOIN events_organizer o ON o.id = e.organizer_id
LEFT JOIN rewards_visit v ON v.event_id = e.id
GROUP BY e.id, o.name
ORDER BY e.updated_at DESC
LIMIT 15;


-- 5. Модерация: события, которые ждут проверки администратора
-- После «Опубликовать» в админке статус меняется на published
SELECT e.id, e.title_en AS event, o.name AS organizer, e.status, e.updated_at
FROM events_event e
JOIN events_organizer o ON o.id = e.organizer_id
WHERE e.status = 'pending'
ORDER BY e.updated_at DESC;


-- 6. Уровни NFT: таблица уровней (меняется в админке)
SELECT name_en, name_ru, name_kk, min_nfts, discount_percent
FROM rewards_loyaltylevel
ORDER BY min_nfts;


-- 7. Уровень каждого пользователя: сколько у него выданных NFT и какой уровень это даёт
SELECT u.username,
       count(n.id) AS nfts,
       (SELECT l.name_en FROM rewards_loyaltylevel l
        WHERE l.min_nfts <= count(n.id) ORDER BY l.min_nfts DESC LIMIT 1) AS level,
       coalesce((SELECT l.discount_percent FROM rewards_loyaltylevel l
                 WHERE l.min_nfts <= count(n.id) ORDER BY l.min_nfts DESC LIMIT 1), 0) AS discount_percent
FROM accounts_user u
JOIN rewards_visit v ON v.user_id = u.id
JOIN rewards_nftreward n ON n.visit_id = v.id AND n.status = 'minted'
GROUP BY u.id
ORDER BY nfts DESC;


-- 8. Коды скидок: выдача и погашение (сайт: «Получить код скидки», «Проверка кода скидки»)
-- status: active → used; used_at и redeemed_by заполняются, когда организатор применил код
SELECT d.code, u.username, e.title_en AS event, d.discount_percent, e.price,
       round(e.price * (100 - d.discount_percent) / 100, 2) AS final_price,
       d.status, d.created_at, d.used_at, r.username AS redeemed_by
FROM rewards_discountcode d
JOIN accounts_user u ON u.id = d.user_id
JOIN events_event e ON e.id = d.event_id
LEFT JOIN accounts_user r ON r.id = d.redeemed_by_id
ORDER BY d.created_at DESC;


-- 9. Поиск: тот же запрос, что делает сайт — только по названиям (подставьте своё слово)
SELECT id, title_en, title_ru, title_kk
FROM events_event
WHERE status = 'published'
  AND (title_en ILIKE '%demo%' OR title_ru ILIKE '%demo%' OR title_kk ILIKE '%demo%');
