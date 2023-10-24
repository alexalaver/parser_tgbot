from aiogram import Bot, Dispatcher, types, executor
import config as cfg
import logging

logging.basicConfig(level=logging.INFO)

bot = Bot(cfg.TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    if message.chat.type == types.ChatType.PRIVATE:
        await message.answer('test')


if __name__ == "__main__":
    executor.start_polling(dp)