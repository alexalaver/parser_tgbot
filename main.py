from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.storage import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from datbas import Data
import config as cfg
import logging

logging.basicConfig(level=logging.INFO)

bot = Bot(cfg.TOKEN, parse_mode=types.ParseMode.MARKDOWN)
dp = Dispatcher(bot, storage=MemoryStorage())
db = Data("localhost", "5432", "parsers", "parser_user", "parser_pwd")


async def profile(message):
    user_id = message.from_user.id
    markup_inline = types.InlineKeyboardMarkup(row_width=1)
    btn_inline1 = types.InlineKeyboardButton(cfg.up_balance, callback_data='up_balance')
    btn_inline2 = types.InlineKeyboardButton(cfg.tariff_selection, callback_data='tariff_selection')
    markup_inline.add(btn_inline1, btn_inline2)
    await message.answer_photo(photo=types.InputFile("img/testphoto.png"), caption=cfg.profile(user_id, 'test', 'test'), reply_markup=markup_inline)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    if message.chat.type == types.ChatType.PRIVATE:
        user_id = message.from_user.id
        first_name = message.from_user.first_name
        username = message.from_user.username
        if(not db.check_user(user_id)):
            db.add_user(user_id, first_name, username)
        markup_reply = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
        markup_reply.add(cfg.autoposting)
        markup_reply.add(cfg.parser)
        markup_reply.row(cfg.my_profile, cfg.support)

        await message.answer('test', reply_markup=markup_reply)
        await profile(message)

@dp.callback_query_handler()
async def buttons_callback(callback_query: types.CallbackQuery):
    if callback_query.data == "tariff_selection":
        markup_inline = types.InlineKeyboardMarkup(row_width=1)
        btn_inline1 = types.InlineKeyboardButton(cfg.start_tariff_button, callback_data='start_tariff')
        btn_inline2 = types.InlineKeyboardButton(cfg.standart_tariff_button, callback_data='standart_tariff')
        btn_inline3 = types.InlineKeyboardButton(cfg.premium_tariff_button, callback_data='premium_tariff')
        btn_inline4 = types.InlineKeyboardButton(cfg.my_profile, callback_data='profile')
        btn_inline5 = types.InlineKeyboardButton(cfg.support, callback_data='support')
        btn_inline6 = types.InlineKeyboardButton(cfg.back_button, callback_data='back_tariff')
        markup_inline.add(btn_inline1, btn_inline2, btn_inline3)
        markup_inline.row(btn_inline4, btn_inline5)
        markup_inline.add(btn_inline6)
        await callback_query.message.edit_caption(caption=cfg.tariff_list, reply_markup=markup_inline)
    elif callback_query.data == "back_tariff":
        user_id = callback_query.from_user.id
        markup_inline = types.InlineKeyboardMarkup(row_width=1)
        btn_inline1 = types.InlineKeyboardButton(cfg.up_balance, callback_data='up_balance')
        btn_inline2 = types.InlineKeyboardButton(cfg.tariff_selection, callback_data='tariff_selection')
        markup_inline.add(btn_inline1, btn_inline2)
        await callback_query.message.edit_caption(caption=cfg.profile(user_id, 'test', 'test'), reply_markup=markup_inline)

@dp.message_handler()
async def other(message: types.Message):
    if message.chat.type == types.ChatType.PRIVATE:
        if message.text == cfg.my_profile:
            await profile(message)

if __name__ == "__main__":
    executor.start_polling(dp)