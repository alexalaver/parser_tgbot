from aiogram import Bot, Dispatcher, types, executor
from datbas import Data
import config as cfg
import logging

logging.basicConfig(level=logging.INFO)

bot = Bot(cfg.TOKEN)
dp = Dispatcher(bot)
db = Data("localhost", "5432", "pars_db", "pars_user", "pars_pwd")

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    if message.chat.type == types.ChatType.PRIVATE:
        user_id = message.from_user.id
        first_name = message.from_user.first_name
        username = message.from_user.username
        if(not db.check_user(user_id)):
            db.add_user(user_id, first_name, username)
        markup_inline = types.InlineKeyboardMarkup(row_width=1)
        btn_inline1 = types.InlineKeyboardButton(cfg.up_balance, callback_data='up_balance')
        btn_inline2 = types.InlineKeyboardButton(cfg.tariff_selection, callback_data='tariff_selection')
        markup_inline.add(btn_inline1, btn_inline2)
        markup_reply = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
        markup_reply.add(cfg.autoposting)
        markup_reply.add(cfg.parser)
        markup_reply.row(cfg.my_profile, cfg.support)

        await message.answer('test', reply_markup=markup_reply)
        await message.answer_photo(photo=types.InputFile("img/testphoto.png"), caption=cfg.profile(user_id, 'test', 'test'), reply_markup=markup_inline)


if __name__ == "__main__":
    executor.start_polling(dp)