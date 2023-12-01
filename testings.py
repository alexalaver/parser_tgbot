import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, PhoneCodeExpiredError, PhoneNumberUnoccupiedError

API_ID = '20150090'
API_HASH = '772e2f003782fc07b0089b0b38c7087c'
BOT_TOKEN = '6597828235:AAH60BBRislfPCqwBeGsiYMBEjXuBrHujZ0'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())
phone_to_client = {}
phone_code_requested = {}

class Form(StatesGroup):
    phone = State()
    code = State()
    password = State()

async def start_telegram_session(phone):
    session = StringSession()
    client = TelegramClient(session, API_ID, API_HASH)
    await client.connect()
    phone_to_client[phone] = client
    return client

@dp.message_handler(commands=['start'], state='*')
async def send_welcome(message: types.Message, state: FSMContext):
    await state.finish()
    await Form.phone.set()
    await message.reply("Привет! Введите ваш номер телефона.")

@dp.message_handler(state=Form.phone, regexp=r'^\+\d+$')
async def phone_number_received(message: types.Message, state: FSMContext):
    phone = message.text
    if phone in phone_code_requested:
        await message.reply("Код уже был отправлен на этот номер. Пожалуйста, введите полученный код.")
        return
    client = await start_telegram_session(phone)
    try:
        await client.send_code_request(phone)
        phone_code_requested[phone] = True
        await Form.next()
        await state.update_data(phone=phone)
        await message.reply("Код авторизации отправлен в Telegram. Введите его здесь.")
    except Exception as e:
        await message.reply(f"Произошла ошибка при отправке кода: {str(e)}")
        await state.finish()

@dp.message_handler(lambda message: message.text.isdigit(), state=Form.code)
async def code_received(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    phone = user_data.get("phone")
    client = phone_to_client.get(phone)
    if client:
        try:
            await client.sign_in(phone, message.text)
            string_session = client.session.save()
            await state.finish()
            del phone_code_requested[phone]
            await message.reply(f"Ваша string session: {string_session}")
        except SessionPasswordNeededError:
            await Form.next()
            await message.reply("Требуется пароль для двухфакторной аутентификации. Введите его здесь.")
        except PhoneCodeExpiredError:
            await message.reply("Код подтверждения истек. Попробуйте начать заново.")
            await state.finish()
        except PhoneNumberUnoccupiedError:
            await message.reply("Этот номер телефона не зарегистрирован в Telegram.")
            await state.finish()
        except Exception as e:
            await message.reply(f"Произошла ошибка: {str(e)}")
            if isinstance(e, PhoneCodeExpiredError):
                del phone_code_requested[phone]
            await state.finish()

@dp.message_handler(state=Form.password)
async def password_received(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    phone = user_data.get("phone")
    client = phone_to_client.get(phone)
    if client:
        try:
            await client.sign_in(password=message.text)
            string_session = client.session.save()
            await state.finish()
            await message.reply(f"Ваша string session: {string_session}")
        except Exception as e:
            await message.reply(str(e))
            await state.finish()

executor.start_polling(dp, skip_updates=True)
