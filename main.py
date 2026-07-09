import os
import json
import asyncio
from pathlib import Path

from aiohttp import web
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import (
    Message,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)

from bot.db import (
    init_db,
    get_catalog,
    toggle_product,
    toggle_flavor,
    update_price,
    create_order,
    get_orders,
    get_order,
    update_order_status,
    add_payment,
    get_setting,
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = int(os.getenv("ADMIN_ID", "5255297864"))
WEBAPP_URL = os.getenv("WEBAPP_URL", "http://localhost:8080").rstrip("/")

if not BOT_TOKEN or BOT_TOKEN == "PASTE_NEW_TOKEN_HERE":
    raise RuntimeError("Нет BOT_TOKEN. Вставь новый токен в .env или переменные хостинга.")

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

def is_admin(user_id):
    return int(user_id) == ADMIN_ID

def main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Открыть магазин", web_app=WebAppInfo(url=f"{WEBAPP_URL}/"))],
            [KeyboardButton(text="📦 Мои заказы")]
        ],
        resize_keyboard=True
    )

def admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛠 Открыть админ-панель", web_app=WebAppInfo(url=f"{WEBAPP_URL}/admin"))],
        [InlineKeyboardButton(text="📦 Заказы", callback_data="orders")]
    ])

def order_keyboard(order_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm:{order_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject:{order_id}")
        ],
        [InlineKeyboardButton(text="📦 Завершить", callback_data=f"complete:{order_id}")]
    ])

def format_order(o):
    items = json.loads(o["items_json"])
    items_text = "\n".join([f"• {x['name']} / {x['flavor']} × {x['qty']} — {x['price']} zł" for x in items])
    return (
        f"📦 <b>Заказ #{o['id']}</b>\n"
        f"Статус: <b>{o['status']}</b>\n"
        f"Сумма: <b>{o['total']} zł</b>\n\n"
        f"Имя: {o['name']}\n"
        f"Ник: @{o['username'] or 'нет'}\n"
        f"Телефон: {o['phone']}\n"
        f"Город: {o['city']}\n"
        f"Адрес: {o['address'] or 'нет'}\n"
        f"Тип: {o['delivery_type']}\n"
        f"Комментарий: {o['comment'] or 'нет'}\n\n"
        f"{items_text}"
    )

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🔞 <b>Cloudix Store</b>\n\n"
        "Продажа только 18+.\n"
        "Оформляя заказ, ты подтверждаешь, что тебе есть 18 лет.\n\n"
        "Нажми кнопку ниже, чтобы открыть магазин.",
        reply_markup=main_keyboard()
    )

@dp.message(Command("admin"))
async def admin(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Нет доступа.")
        return
    await message.answer("🛠 <b>Админ-панель</b>", reply_markup=admin_keyboard())

@dp.message(F.text == "📦 Мои заказы")
async def my_orders(message: Message):
    orders = await get_orders(user_id=message.from_user.id)
    if not orders:
        await message.answer("Заказов пока нет.")
        return
    text = "📦 <b>Твои заказы:</b>\n\n" + "\n".join([f"#{o['id']} — {o['total']} zł — {o['status']}" for o in orders])
    await message.answer(text)

@dp.message(F.photo)
async def photo_payment(message: Message):
    caption = message.caption or ""
    if not caption.startswith("/pay"):
        await message.answer("Для скрина оплаты отправь фото с подписью: <code>/pay номер_заказа</code>")
        return

    parts = caption.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Пример подписи: <code>/pay 1</code>")
        return

    order_id = int(parts[1])
    order = await get_order(order_id)
    if not order or int(order["user_id"]) != message.from_user.id:
        await message.answer("Не нашёл такой заказ у тебя.")
        return

    file_id = message.photo[-1].file_id
    await add_payment(order_id, file_id)

    await message.answer(f"✅ Скрин прикреплён к заказу #{order_id}. Ожидай подтверждения.")
    await bot.send_message(ADMIN_ID, f"💳 Скрин оплаты для заказа #{order_id}", reply_markup=order_keyboard(order_id))
    await bot.send_photo(ADMIN_ID, file_id, caption=f"Скрин оплаты заказа #{order_id}")

@dp.callback_query(F.data == "orders")
async def orders_cb(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    orders = await get_orders()
    if not orders:
        await callback.message.answer("Заказов нет.")
        await callback.answer()
        return
    for o in orders[:10]:
        await callback.message.answer(format_order(o), reply_markup=order_keyboard(o["id"]))
    await callback.answer()

@dp.callback_query(F.data.startswith("confirm:"))
async def confirm_cb(callback: CallbackQuery):
    order_id = int(callback.data.split(":")[1])
    order = await get_order(order_id)
    if not order:
        await callback.answer("Не найдено", show_alert=True)
        return
    await update_order_status(order_id, "confirmed")
    await bot.send_message(order["user_id"], f"✅ Заказ #{order_id} подтверждён.")
    await callback.message.answer(f"✅ Заказ #{order_id} подтверждён.")
    await callback.answer()

@dp.callback_query(F.data.startswith("reject:"))
async def reject_cb(callback: CallbackQuery):
    order_id = int(callback.data.split(":")[1])
    order = await get_order(order_id)
    if not order:
        await callback.answer("Не найдено", show_alert=True)
        return
    await update_order_status(order_id, "rejected")
    await bot.send_message(order["user_id"], f"❌ Заказ #{order_id} отклонён.")
    await callback.message.answer(f"❌ Заказ #{order_id} отклонён.")
    await callback.answer()

@dp.callback_query(F.data.startswith("complete:"))
async def complete_cb(callback: CallbackQuery):
    order_id = int(callback.data.split(":")[1])
    order = await get_order(order_id)
    if not order:
        await callback.answer("Не найдено", show_alert=True)
        return
    await update_order_status(order_id, "completed")
    await bot.send_message(order["user_id"], f"📦 Заказ #{order_id} завершён.")
    await callback.message.answer(f"📦 Заказ #{order_id} завершён.")
    await callback.answer()

async def index(request):
    return web.FileResponse(Path("webapp/index.html"))

async def admin_page(request):
    return web.FileResponse(Path("webapp/admin.html"))

async def api_catalog(request):
    admin = request.query.get("admin") == "1"
    return web.json_response({"ok": True, "catalog": await get_catalog(admin=admin)})

async def api_settings(request):
    return web.json_response({
        "ok": True,
        "payment_text": await get_setting("payment_text"),
        "rules_text": await get_setting("rules_text"),
        "delivery": {
            "pickup_city": "Величка",
            "pickup_place": "дом пушкина дом калатушкина",
            "city_delivery_price": 15,
            "other_city_delivery_price": 20
        }
    })

async def api_order(request):
    data = await request.json()
    order_id = await create_order(data)
    await bot.send_message(
        data["user_id"],
        f"🧾 Заказ #{order_id} создан.\n"
        f"Сумма: <b>{data['total']} zł</b>\n\n"
        f"После оплаты отправь скрин фото с подписью:\n"
        f"<code>/pay {order_id}</code>"
    )
    await bot.send_message(ADMIN_ID, f"🆕 Новый заказ #{order_id}\nСумма: {data['total']} zł", reply_markup=order_keyboard(order_id))
    return web.json_response({"ok": True, "order_id": order_id})

async def api_admin_orders(request):
    orders = await get_orders()
    result = []
    for o in orders:
        x = dict(o)
        x["items"] = json.loads(o["items_json"])
        result.append(x)
    return web.json_response({"ok": True, "orders": result})

async def api_toggle_product(request):
    data = await request.json()
    await toggle_product(int(data["product_id"]))
    return web.json_response({"ok": True})

async def api_toggle_flavor(request):
    data = await request.json()
    await toggle_flavor(int(data["flavor_id"]))
    return web.json_response({"ok": True})

async def api_update_price(request):
    data = await request.json()
    await update_price(int(data["product_id"]), int(data["price"]))
    return web.json_response({"ok": True})

async def api_order_status(request):
    data = await request.json()
    order_id = int(data["order_id"])
    status = data["status"]
    await update_order_status(order_id, status)
    order = await get_order(order_id)
    if order:
        await bot.send_message(order["user_id"], f"📦 Статус заказа #{order_id}: <b>{status}</b>")
    return web.json_response({"ok": True})

async def make_app():
    await init_db()
    app = web.Application()
    app.router.add_get("/", index)
    app.router.add_get("/admin", admin_page)
    app.router.add_static("/static", Path("webapp"))

    app.router.add_get("/api/catalog", api_catalog)
    app.router.add_get("/api/settings", api_settings)
    app.router.add_post("/api/order", api_order)
    app.router.add_get("/api/admin/orders", api_admin_orders)
    app.router.add_post("/api/admin/toggle-product", api_toggle_product)
    app.router.add_post("/api/admin/toggle-flavor", api_toggle_flavor)
    app.router.add_post("/api/admin/update-price", api_update_price)
    app.router.add_post("/api/admin/order-status", api_order_status)

    async def startup(app):
        await bot.delete_webhook(drop_pending_updates=True)
        app["polling"] = asyncio.create_task(dp.start_polling(bot))

    async def cleanup(app):
        app["polling"].cancel()
        await bot.session.close()

    app.on_startup.append(startup)
    app.on_cleanup.append(cleanup)
    return app

if __name__ == "__main__":
    web.run_app(make_app(), host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
