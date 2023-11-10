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

a = ['testing !', 'loveyou !', "odin ?", "dva ?", "privetiki !"]
new_list = [item for item in a if item.endswith('!')]
print(new_list)