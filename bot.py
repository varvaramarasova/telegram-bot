import asyncio
import requests
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.exceptions import TelegramAPIError

TOKEN = os.getenv("BOT_TOKEN")        
API_KEY = os.getenv("WEATHER_API_KEY") 
CHANNEL = "@d2trip"                 
ADMIN_ID = 2015990328               

bot = Bot(token=TOKEN)
dp = Dispatcher()

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is running!")

@dp.message()
async def handle_all(message: types.Message):
    # 1️⃣ Пересылаем админу
    try:
        await bot.send_message(
            ADMIN_ID,
            f"Сообщение от {message.from_user.full_name} "
            f"(@{message.from_user.username}):\n{message.text}"
        )
    except Exception as e:
        print(f"Ошибка при пересылке админу: {e}")

    # 2️⃣ Обработка кнопок
    if message.text == "Получить подборку":
        await message.answer(
            "Вот твоя награда\n\n"
            "1️⃣ спасибо\n"
            "2️⃣ большое\n"
            "3️⃣ данисик\n"
            "4️⃣ ты\n"
            "5️⃣ хорошка"
        )
    elif message.text == "Узнать погоду":
        await message.answer("Напиши название города, чтобы узнать погоду 🌤")
    else:
        # Погода
        city = message.text.strip()
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric&lang=ru"
            data = requests.get(url, timeout=10).json()
            if data.get("cod") != 200:
                await message.answer("Не могу найти такой город 😔 Проверь название.")
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
                f"💨 Ветер: {wind} м/с"
            )
        except Exception as e:
            await message.answer(f"Ошибка при получении погоды: {e}")

async def main():
    # Polling бота
    polling_task = asyncio.create_task(dp.start_polling(bot, skip_updates=True))
    
    # HTTP сервер для Render
    port = int(os.getenv("PORT", 10000))
    http_server = HTTPServer(("0.0.0.0", port), Handler)
    server_task = asyncio.to_thread(http_server.serve_forever)
    
    await asyncio.gather(polling_task, server_task)

if __name__ == "__main__":
    asyncio.run(main())
