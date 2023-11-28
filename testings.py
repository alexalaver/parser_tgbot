from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from telethon import TelegramClient
from telethon.sessions import StringSession

API_ID = '20150090'  # Замените на ваш Telegram API ID
API_HASH = '772e2f003782fc07b0089b0b38c7087c'  # Замените на ваш Telegram API Hash
BOT_TOKEN = '6597828235:AAH60BBRislfPCqwBeGsiYMBEjXuBrHujZ0'  # Замените на токен вашего бота

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

client = TelegramClient(StringSession(), API_ID, API_HASH)

# Глобальная переменная для хранения phone_code_hash
phone_code_hash = None

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Отправь мне свой номер телефона для верификации.")

@dp.message_handler(commands=['cancel'])
async def cancel_handler(message: types.Message):
    await message.reply('Верификация отменена.')

@dp.message_handler()
async def process_message(message: types.Message):
    global phone_code_hash  # Объявляем переменную как глобальную

    if not client.is_connected():
        await client.connect()

    if message.text.startswith('+'):  # Предполагаем, что это номер телефона
        try:
            result = await client.send_code_request(message.text)
            await message.reply("Отправьте код, который вы получили от Telegram.")
            phone_code_hash = result.phone_code_hash
        except Exception as e:
            await message.reply(f"Ошибка: {e}")

    else:  # Предполагаем, что это код подтверждения
        try:
            await client.sign_in(message.text, phone_code_hash=phone_code_hash)
            string_session = client.session.save()
            await message.reply(f"Ваш Session String: {string_session}")
        except Exception as e:
            await message.reply(f"Ошибка аутентификации: {e}")

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)