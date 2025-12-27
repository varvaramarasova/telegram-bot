import os
import asyncio
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.exceptions import TelegramAPIError
from aiohttp import web

TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("WEATHER_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", "2015990328"))

WEBHOOK_HOST = os.getenv("WEBHOOK_URL")  # https://your-render-url.onrender.com
WEBHOOK_PATH = f"/webhook/{TOKEN}"
WEBHOOK_URL = WEBHOOK_HOST + WEBHOOK_PATH

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()


# ------------------ КЛАВИАТУРЫ ---------------------
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Получить подборку")],
            [KeyboardButton(text="Узнать погоду")]
        ],
        resize_keyboard=True
    )
    return keyboard


# ------------------ ОБРАБОТЧИКИ ---------------------

@dp.message(Command("start"))
async def start(message: types.Message):
    keyboard = get_main_keyboard()
    await message.answer(
        "Бот работает через Render Webhook! ✨",
        reply_markup=keyboard
    )


@dp.message()
async def handle_all(message: types.Message):

    # Пересылаем админу
    try:
        await bot.send_message(
            ADMIN_ID,
            f"Сообщение от {message.from_user.full_name} (@{message.from_user.username}):\n{message.text}"
        )
    except Exception as e:
        print("Ошибка админу:", e)

    if message.text == "Получить подборку":
        await message.answer(
            "Вот твоя награда\n\n"
            "1️⃣ спасибо\n"
            "2️⃣ большое\n"
            "3️⃣ данисик\n"
            "4️⃣ ты\n"
            "5️⃣ хорошка",
            reply_markup=get_main_keyboard()
        )
        return

    if message.text == "Узнать погоду":
        await message.answer("Напиши город 🌤", reply_markup=get_main_keyboard())
        return

    # Погода
    city = message.text.strip()
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric&lang=ru"
        data = requests.get(url, timeout=10).json()

        if data.get("cod") != 200:
            await message.answer("Не могу найти такой город 😔", reply_markup=get_main_keyboard())
            return

        desc = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        wind = data["wind"]["speed"]

        await message.answer(
            f"Погода в {city}:\n"
            f"{desc}\n"
            f"🌡 Температура: {temp}°C\n"
            f"💧 Влажность: {humidity}%\n"
            f"💨 Ветер: {wind} м/с",
            reply_markup=get_main_keyboard()
        )

    except Exception as e:
        await message.answer(f"Ошибка погоды: {e}", reply_markup=get_main_keyboard())


# ------------------ WEBHOOK ---------------------

async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)
    print("Webhook установлен:", WEBHOOK_URL)


async def on_shutdown(app):
    await bot.delete_webhook()
    await bot.session.close()   # <-- фикс Unclosed session


async def handle_webhook(request: web.Request):
    update = await request.json()
    await dp.feed_webhook_update(bot, update)
    return web.Response()


async def health(request):
    return web.Response(text="Bot is running!")


def main():
    app = web.Application()

    app.router.add_get("/", health)
    app.router.add_post(WEBHOOK_PATH, handle_webhook)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    port = int(os.getenv("PORT", 10000))
    web.run_app(app, host="0.0.0.0", port=port)


# ❗ правильная строка (у тебя была сломана)
if __name__ == "__main__":
    main()
