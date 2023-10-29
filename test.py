import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from telethon.sync import TelegramClient
from telethon.tl.types import InputChannel
from telethon.tl.functions.messages import SearchRequest

# Ваш токен бота
BOT_TOKEN = 'YOUR_BOT_TOKEN'

# Ваши параметры авторизации для Telethon
API_ID = '29417722'
API_HASH = 'YOUR_API_HASH'

# Инициализируем Telegram бота и клиент Telethon
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)
loop = asyncio.get_event_loop()

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Привет! Этот бот поможет вам парсить посты из каналов по ключевым словам. "
                         "Для начала, пожалуйста, отправьте мне имя канала в формате @название_канала.")

# Обработчик текстового сообщения с именем канала
@dp.message_handler(lambda message: message.text.startswith('@'))
async def get_keyword(message: types.Message):
    chat_id = message.chat.id
    channel_name = message.text
    await message.answer("Теперь введите ключевое слово для поиска в постах.")

    # Ожидаем следующего сообщения с ключевым словом
    @dp.message_handler(lambda message: message.text)
    async def get_posts(message: types.Message):
        keyword = message.text
        await message.answer(f"Ищу посты в канале {channel_name} по ключевому слову '{keyword}'...")

        # Используем Telethon для получения постов из канала
        with TelegramClient('session_name', API_ID, API_HASH) as client:
            try:
                channel_entity = await client.get_entity(channel_name)
                channel_id = InputChannel(channel_entity, channel_entity.access_hash)
                messages = await client(SearchRequest(peer=channel_id, q=keyword, limit=10))
                await message.answer(f"Результаты поиска в канале {channel_name}:")
                for post in messages.messages:
                    await message.answer(post.text, parse_mode='html')
            except Exception as e:
                await message.answer(f"Произошла ошибка: {str(e)}")

    # Удаляем обработчик после использования
    dp.remove_message_handler(get_posts)

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
