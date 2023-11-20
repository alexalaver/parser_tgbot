# from aiogram import Bot, Dispatcher, types, executor
# import datetime
#
# bot = Bot("6814346342:AAG6Yd6zyF-eKUKK7UCMQgeZG4YqIgwGrBw")
# dp = Dispatcher(bot)
#
# @dp.message_handler(commands=['start'])
# async def start_command(message: types.Message):
#     current_date = datetime.datetime.now()
#     formatted_date = current_date.strftime("%Y-%m-%d %H:%M:%S")
#     await message.answer(formatted_date)
#
# @dp.message_handler()
# async def texts(message: types.Message):
#     if message.text == "hello":
#         current_date = datetime.datetime.now()
#         new_date = current_date + datetime.timedelta(days=30)
#         formatted_date = current_date.strftime("%Y-%m-%d %H:%M:%S")
#         formatted_date_new = new_date.strftime("%Y-%m-%d %H:%M:%S")
#         await message.answer(f"Сейчас: {formatted_date}\nЧерез месяц: {formatted_date_new}")
#     elif message.text == "eshe":
#         a = "2023-11-29 18:23:26"
#         b = datetime.datetime.strptime(a, "%Y-%m-%d %H:%M:%S")
#         new_date = b + datetime.timedelta(days=30)
#         formated_date = new_date.strftime("%Y-%m-%d %H:%M:%S")
#         await message.answer(formated_date)
#     elif message.text == "proverka":
#         current_data = datetime.datetime.now()
#         date_is_base = "2023-10-25 18:23:26"
#         formated_base = datetime.datetime.strptime(date_is_base, "%Y-%m-%d %H:%M:%S")
#         if current_data >= formated_base:
#             await message.answer("Тариф прошёл")
#         elif current_data < formated_base:
#             await message.answer("Тариф не прошёл")
#     else:
#         textsing = message.text
#         text_lines = textsing.strip().split('\n')
#         await message.answer(f"{len(text_lines)}")
#
# if __name__ == "__main__":
#     executor.start_polling(dp)
#
#
# import asyncio
# import logging
# from aiogram import Bot, Dispatcher, executor, types
# from telethon import TelegramClient, events
# from telethon.sessions import StringSession
#
# # Настройка логгирования
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
#
# API_TOKEN = '6814346342:AAG6Yd6zyF-eKUKK7UCMQgeZG4YqIgwGrBw'
#
# API_ID = '26080110'
# API_HASH = 'bc09aee3b4cbedb0351a379cd3571215'
#
# STRING_SESSION = '1BJWap1sBuyLY8yUCD8WEl1KZiRfaKp61jq3SrrJrd3tVYiFSkd6tyl6tuR6B4SskVOYyUu-ZjYtwTYqIeZo4H3rvI2SgPqO1RDrIlSReDP06qgxBG7k2IF53JVo-EuXmsjqduyM1PDrqEw45bRJdONFObLwdtJZiBN4qtWcksvN4U9MbwzjGE8MIxJ86wfRlknGOU88WC38lwOlE5LHTItCUs9UTrKLsvKGwwi6ImD1yfUWe1KvIgmCyCFmAkc18zNk7RJPLhV1tteMdHsc9hwIC_snGHeCCGgfFpknn80Ko3NMudVkzpz5ntESwe3YX7xywi2n0rTq0aMBatN9feFarXpqSPsM='
#
# chat_ids = ["@mediapartisanschat"]
# keywords = ['Армения']
#
# # Инициализация aiogram
# bot = Bot(token=API_TOKEN)
# dp = Dispatcher(bot)
#
# # Инициализация Telethon
# telethon_client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
#
# async def search_and_forward(user_id):
#     try:
#         await telethon_client.start()
#         async with telethon_client:
#             for chat_id in chat_ids:
#                 async for message in telethon_client.iter_messages(chat_id):
#                     if any(keyword.lower() in (message.text or "").lower() for keyword in keywords):
#                         await bot.send_message(user_id, message.text)
#                         logger.info(f"Сообщение отправлено пользователю {user_id}: {message.text}")
#     except Exception as e:
#         logger.error(f"Ошибка при выполнении поиска и пересылки: {e}")
#
# @dp.message_handler(commands=['start'])
# async def send_welcome(message: types.Message):
#     user_id = message.from_user.id
#     await message.reply("Начинается мониторинг чатов...")
#     logger.info(f"Команда /start получена от пользователя {user_id}")
#     asyncio.create_task(search_and_forward(user_id))
#
# if __name__ == '__main__':
#     executor.start_polling(dp, skip_updates=True)

#
# for i in range(1, 51):
#     print(f"test{str(i)}")

# a = ["https://t.me/+_xedHrVHkr85YzFh ⏳","https://t.me/+UOewsTV7LtxhOWYx ⏳","https://t.me/test2asodjas ✅","https://t.me/test4publiccc ✅","https://t.me/+Y2KY3rg483xkZTEx ⏳","https://t.me/test6publicc ✅","https://t.me/test6publiccc ✅","https://t.me/+XftdKHLmXXZjNTZh ⏳","https://t.me/+RIn2HNSK4YxhOWUx ⏳","https://t.me/+OixTZDaRnJoyMGNh ⏳"]
# chat_ids = [item for item in a if len(item) >= 1 and item[13] == '+']
# print(chat_ids)

# a = ["https://t.me/+a3UxfURmNGA0Zjgy ✅","https://t.me/+F5C9DROFADo4NWNi ✅","https://t.me/+OF5wBCw4OTsxZjMy ✅","https://t.me/+lKwO7uUR26ZkZjU6 ✅","https://t.me/+kaLhqGj2EHg3NjFi ✅","https://t.me/+seW1RLuAcPJhYjNi ⏳","@jivichatt ✅"]
# channels_link = [item for item in a if len(item) >= 13 and item[13] == '+']
# print(channels_link)

# a = '1. hello bro'
# print(a[3:])

# a = ["https://t.me/+OixTZDaRnJoyMGNh ✅", "https://t.me/+Y2KY3rg483xkZTEx ✅", "https://t.me/+RIn2HNSK4YxhOWUx ✅", "https://t.me/+AACeCS2QF4BiODM6 ✅", "https://t.me/+qgMQu0WCBhphNzg0 ✅"]
# b = ["1. 4654646", "4. 6545654", "3. 4654645"]  # Предполагаем, что все элементы преобразованы в строки
#
# for item in b:
#     index = int(item.split('.')[0]) - 1  # Вычисляем индекс (уменьшаем на 1, так как индексация в Python начинается с 0)
#     a[index] = a[index].replace("✅", "X")  # Заменяем "✅" на "X"
#
# print(a)

# a = "1) hello"
# print(a[3:])
import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from telethon import TelegramClient
from telethon.sessions import StringSession

API_TOKEN = '6597828235:AAH60BBRislfPCqwBeGsiYMBEjXuBrHujZ0'
api_id = '20150090'
api_hash = '772e2f003782fc07b0089b0b38c7087c'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

class AuthState(StatesGroup):
    phone = State()
    code = State()
    phone_code_hash = State()

telethon_client = TelegramClient(StringSession(), api_id, api_hash)

async def connect_telethon_client():
    if not telethon_client.is_connected():
        await telethon_client.connect()

@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    await connect_telethon_client()
    await AuthState.phone.set()
    await message.reply("Пожалуйста, отправьте свой номер телефона в формате +123456789")

@dp.message_handler(state=AuthState.phone)
async def process_phone(message: types.Message, state: FSMContext):
    try:
        result = await telethon_client.send_code_request(phone=message.text)
        async with state.proxy() as data:
            data['phone'] = message.text
            data['phone_code_hash'] = result.phone_code_hash
        await AuthState.next()
        await message.reply("Теперь отправьте код, который вы получили от Telegram")
    except Exception as e:
        logging.error(f"Ошибка при отправке кода: {e}")
        await message.reply("Произошла ошибка при отправке кода, пожалуйста, попробуйте еще раз.")

@dp.message_handler(state=AuthState.code)
async def process_code(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        phone = data['phone']
        phone_code_hash = data['phone_code_hash']
    try:
        await telethon_client.sign_in(phone=phone, code=message.text, phone_code_hash=phone_code_hash)
        string_session = telethon_client.session.save()
        await message.reply(f"Аутентификация успешна! Ваш StringSession: {string_session}")
    except Exception as e:
        logging.error(f"Ошибка при аутентификации: {e}")
        await message.reply(f"Ошибка аутентификации: {e}")

if __name__ == '__main__':
    executor.start_polling(dp)


