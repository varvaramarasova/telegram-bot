import os
import asyncio
import requests
from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, Update
from aiogram.exceptions import TelegramAPIError
from aiohttp import web
from aiohttp.web_exceptions import HTTPBadRequest

TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("WEATHER_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", "2015990328"))

WEBHOOK_HOST = os.getenv("WEBHOOK_URL")
WEBHOOK_PATH = f"/webhook/{TOKEN}"
WEBHOOK_URL = WEBHOOK_HOST + WEBHOOK_PATH

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Клавиатуры
def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Получить подборку")],
            [KeyboardButton(text="Узнать погоду")]
        ],
        resize_keyboard=True
    )

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Бот работает через Render Webhook! ✨",
        reply_markup=get_main_keyboard()
    )

@dp.message(F.text == "Получить подборку")
async def selection(message: types.Message):
    await message.answer(
        "Вот твоя награда\n\n"
        "1️⃣ спасибо\n2️⃣ большое\n3️⃣ данисик\n4️⃣ ты\n5️⃣ хорошка",
        reply_markup=get_main_keyboard()
    )

@dp.message(F.text == "Узнать погоду")
async def weather_request(message: types.Message):
    await message.answer("Напиши город 🌤", reply_markup=get_main_keyboard())

@dp.message()
async def weather(message: types.Message):
    # Пересылаем админу
    try:
        await bot.send_message(
            ADMIN_ID,
            f"Сообщение от {message.from_user.full_name} (@{message.from_user.username}):\n{message.text}"
        )
    except:
        pass

    city = message.text.strip()
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city, "appid": API_KEY, 
            "units": "metric", "lang": "ru"
        }
        data = requests.get(url, params=params, timeout=10).json()

        if data.get("cod") != 200:
            await message.answer("Не могу найти такой город 😔", reply_markup=get_main_keyboard())
            return

        desc = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        wind = data["wind"]["speed"]

        await message.answer(
            f"Погода в <b>{city}</b>:\n"
            f"{desc.title()}\n"
            f"🌡 <b>{temp}°C</b>\n"
            f"💧 Влажность: <b>{humidity}%</b>\n"
            f"💨 Ветер: <b>{wind} м/с</b>",
            reply_markup=get_main_keyboard()
        )
    except Exception:
        await message.answer("Ошибка получения погоды 😔", reply_markup=get_main_keyboard())

async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)
    print(f"Webhook установлен: {WEBHOOK_URL}")

async def on_shutdown(app):
    await bot.delete_webhook()
    await bot.session.close()

# ✅ ИСПРАВЛЕННЫЙ webhook handler для aiogram v3
async def handle_webhook(request: web.Request):
    try:
        # Правильная обработка Telegram JSON
        if not request.headers.get("content-type") == "application/json":
            return web.Response(status=400)
        
        json_data = await request.json()
        update = Update.model_validate(json_data)
        await dp.feed_update(bot, update)
        return web.Response(status=200)
    except Exception:
        raise HTTPBadRequest()

async def health(request):
    return web.Response(text="Bot is alive!")

def main():
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_post(WEBHOOK_PATH, handle_webhook)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    
    port = int(os.getenv("PORT", 10000))
    web.run_app(app, host="0.0.0.0", port=port, access_log=None)

if __name__ == "__main__":
    main()
