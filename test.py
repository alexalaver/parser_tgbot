from aiogram import Bot, Dispatcher, types, executor
import datetime

bot = Bot("6814346342:AAG6Yd6zyF-eKUKK7UCMQgeZG4YqIgwGrBw")
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    current_date = datetime.datetime.now()
    formatted_date = current_date.strftime("%Y-%m-%d %H:%M:%S")
    await message.answer(formatted_date)

@dp.message_handler()
async def texts(message: types.Message):
    if message.text == "hello":
        current_date = datetime.datetime.now()
        new_date = current_date + datetime.timedelta(days=30)
        formatted_date = current_date.strftime("%Y-%m-%d %H:%M:%S")
        formatted_date_new = new_date.strftime("%Y-%m-%d %H:%M:%S")
        await message.answer(f"Сейчас: {formatted_date}\nЧерез месяц: {formatted_date_new}")
    elif message.text == "eshe":
        a = "2023-11-29 18:23:26"
        b = datetime.datetime.strptime(a, "%Y-%m-%d %H:%M:%S")
        new_date = b + datetime.timedelta(days=30)
        formated_date = new_date.strftime("%Y-%m-%d %H:%M:%S")
        await message.answer(formated_date)
    elif message.text == "proverka":
        current_data = datetime.datetime.now()
        date_is_base = "2023-10-25 18:23:26"
        formated_base = datetime.datetime.strptime(date_is_base, "%Y-%m-%d %H:%M:%S")
        if current_data >= formated_base:
            await message.answer("Тариф прошёл")
        elif current_data < formated_base:
            await message.answer("Тариф не прошёл")

if __name__ == "__main__":
    executor.start_polling(dp)