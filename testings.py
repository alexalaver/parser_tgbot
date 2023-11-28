from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, PasswordHashInvalidError
from telethon.network import ConnectionTcpMTProxyRandomizedIntermediate
from aiogram.contrib.fsm_storage.memory import MemoryStorage

API_ID = '20150090'  # Замените на ваш Telegram API ID
API_HASH = '772e2f003782fc07b0089b0b38c7087c'  # Замените на ваш Telegram API Hash
BOT_TOKEN = '6597828235:AAH60BBRislfPCqwBeGsiYMBEjXuBrHujZ0'  # Замените на токен вашего бота

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

proxy_host = '168.181.53.247'  # IP-адрес прокси-сервера
proxy_port = 8000  # Порт прокси-сервера
proxy_secret = "st7zNT"
client = TelegramClient(StringSession(), API_ID, API_HASH,
                        connection=ConnectionTcpMTProxyRandomizedIntermediate,
                        proxy=(proxy_host, proxy_port, proxy_secret))
# Определение состояний для FSM
class VerificationState(StatesGroup):
    waiting_for_phone_number = State()
    waiting_for_telegram_code = State()
    waiting_for_2fa_password = State()

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await VerificationState.waiting_for_phone_number.set()
    await message.reply("Привет! Отправь мне свой номер телефона для верификации.")

@dp.message_handler(commands=['cancel'], state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await message.reply('Верификация отменена.')

@dp.message_handler(state=VerificationState.waiting_for_phone_number)
async def process_phone_number(message: types.Message, state: FSMContext):
    phone_number = message.text
    await state.update_data(phone_number=phone_number)

    if not client.is_connected():
        await client.connect()

    try:
        result = await client.send_code_request(phone_number)
        await VerificationState.waiting_for_telegram_code.set()
        await state.update_data(phone_code_hash=result.phone_code_hash)
        await message.reply("Отправьте код, который вы получили от Telegram.")
    except Exception as e:
        await message.reply(f"Ошибка: {e}")
        await state.finish()

@dp.message_handler(state=VerificationState.waiting_for_telegram_code)
async def process_telegram_code(message: types.Message, state: FSMContext):
    code = message.text
    user_data = await state.get_data()
    phone_number = user_data['phone_number']
    phone_code_hash = user_data['phone_code_hash']

    try:
        await client.sign_in(phone_number, code, phone_code_hash=phone_code_hash)
    except SessionPasswordNeededError:
        await VerificationState.waiting_for_2fa_password.set()
        await message.reply("Требуется ввести пароль для двухфакторной аутентификации.")
    except Exception as e:
        await message.reply(f"Ошибка аутентификации: {e}")
        await state.finish()
    else:
        string_session = client.session.save()
        await state.finish()
        await message.reply(f"Ваш Session String: {string_session}")

@dp.message_handler(state=VerificationState.waiting_for_2fa_password)
async def process_2fa_password(message: types.Message, state: FSMContext):
    password = message.text
    try:
        await client.sign_in(password=password)
        string_session = client.session.save()
        await state.finish()
        await message.reply(f"Ваш Session String: {string_session}")
    except PasswordHashInvalidError:
        await message.reply("Неверный пароль, попробуйте еще раз.")
    except Exception as e:
        await message.reply(f"Ошибка при вводе пароля: {e}")
        await state.finish()

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)