# Cloudix Store Mini App

Telegram бот + Telegram Mini App магазин + админ-панель.

## ВАЖНО

Токен, который ты отправил в чат, нужно перевыпустить ещё раз в @BotFather:
`/revoke`

Потом новый токен вставить только в настройки хостинга, не в чат.

## Что уже настроено

Админ ID:
5255297864

Товары:
1. Elfliq — 45 zł — 50 mg
   - blueberry
   - raspberry

2. Vozol Prime — 50 zł — 50 mg
   - blueberry sour raspberry
   - strawberry

Доставка:
- Самовывоз: Величка, дом пушкина дом калатушкина
- Доставка по городу: 15 zł
- Доставка в другой город Польши: 20 zł

Правила:
Продажа только 18+.
Заказ подтверждается админом после проверки оплаты.

## Как запустить локально

1. Установить Python
2. Открыть папку проекта в терминале
3. Выполнить:

```bash
pip install -r requirements.txt
cp .env.example .env
python main.py
```

В `.env` вставить новый токен.

## Для Render/VPS

Переменные окружения:
- BOT_TOKEN
- ADMIN_ID
- WEBAPP_URL
