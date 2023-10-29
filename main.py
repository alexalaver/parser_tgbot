from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.storage import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from datbas import Data
import functions as fnc
import config as cfg
import logging

logging.basicConfig(level=logging.INFO)

bot = Bot(cfg.TOKEN, parse_mode=types.ParseMode.MARKDOWN)
dp = Dispatcher(bot, storage=MemoryStorage())
db = Data("159.69.75.46", "43652", "pars_db", "pars_user", "pars_pwd")


async def profile(message):
    user_id = message.from_user.id
    markup_inline = types.InlineKeyboardMarkup(row_width=1, )
    btn_inline1 = types.InlineKeyboardButton(cfg.up_balance, callback_data='up_balance')
    btn_inline2 = types.InlineKeyboardButton(cfg.tariff_selection, callback_data='tariff_selection')
    markup_inline.add(btn_inline1, btn_inline2)
    await message.answer_photo(photo=types.InputFile("img/testphoto.png"), caption=cfg.profile(user_id, db.select_balance(user_id), db.select_tariffe(user_id)), reply_markup=markup_inline)

async def supports_send(message):
    markup_inline = types.InlineKeyboardMarkup(row_width=1)
    btn_inline1 = types.InlineKeyboardButton(cfg.support, callback_data='support', url="tg://user?id=1076482828")
    markup_inline.add(btn_inline1)
    await message.answer("При индивидуальных запросах или возникновение трудностей, обратитесь по контакту ниже", reply_markup=markup_inline)

async def parsers_send(message):
    markup_inline = types.InlineKeyboardMarkup(row_width=1)
    btn_inline1 = types.InlineKeyboardButton(cfg.chats_button, callback_data='chats_button')
    btn_inline2 = types.InlineKeyboardButton(cfg.word_poisk_button, callback_data='word_poisk_button')
    markup_inline.add(btn_inline1, btn_inline2)
    await message.answer_photo(photo=types.InputFile("img/testphoto.png"), caption=cfg.parser_text, reply_markup=markup_inline)

async def autoposting_send(message):
    markup_inline = types.InlineKeyboardMarkup(row_width=1)
    btn_inline1 = types.InlineKeyboardButton(cfg.account_button, callback_data='accounts_button')
    btn_inline2 = types.InlineKeyboardButton(cfg.posts_button, callback_data='posts_button')
    markup_inline.add(btn_inline1, btn_inline2)
    await message.answer_photo(photo=types.InputFile("img/testphoto.png"), caption=cfg.autoposting_text, reply_markup=markup_inline)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    if message.chat.type == types.ChatType.PRIVATE:
        user_id = message.from_user.id
        first_name = message.from_user.first_name
        username = message.from_user.username
        if(not db.check_user(user_id)):
            db.add_user(user_id, first_name, username)
        markup_reply = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
        markup_reply.add(cfg.autoposting)
        markup_reply.add(cfg.parser)
        markup_reply.row(cfg.my_profile, cfg.support)

        await message.answer('test', reply_markup=markup_reply)
        await profile(message)

@dp.message_handler(commands=['addadmin'])
async def add_admin_user(message: types.Message):
    if message.chat.type == types.ChatType.PRIVATE:
        user_id = message.from_user.id
        if db.select_admin(user_id) > 0:
            select_adm_id = int(message.text.split()[1])
            if(not db.check_user(select_adm_id)):
                await message.answer(cfg.error_not_found_user)
            elif db.check_user(select_adm_id):
                db.add_admin(select_adm_id)
                await message.answer(cfg.right_add_admin(fnc.nick_with_link("администратора", select_adm_id)))
                await dp.bot.send_message(select_adm_id, cfg.take_adm)
            else:
                await message.answer(cfg.error_command)
        else:
            await message.answer(cfg.error_adm_dostup)


@dp.message_handler(commands=['balance'])
async def balance_user(message: types.Message):
    if message.chat.type == types.ChatType.PRIVATE:
        user_id = message.from_user.id
        if db.select_admin(user_id) > 0:
            select_adm_id = message.text.split()
            if len(select_adm_id) == 2:
                if int(select_adm_id[1]):
                    select_adm_id = int(message.text.split()[1])
                    if(not db.check_user(select_adm_id)):
                        await message.answer(cfg.error_not_found_user)
                    elif db.check_user(select_adm_id):
                        balance_user = db.select_balance(select_adm_id)
                        await message.answer(cfg.balance_user_text(fnc.nick_with_link("пользователя", select_adm_id), str(balance_user)))
                else:
                    await message.answer(cfg.balance_command_error)
            else:
                await message.answer(cfg.error_command)
        else:
            await message.answer(cfg.error_adm_dostup)

@dp.message_handler(commands=['addbalance'])
async def addbalance_user(message: types.Message):
    if message.chat.type == types.ChatType.PRIVATE:
        user_id = message.from_user.id
        if db.select_admin(user_id) > 0:
            select_info = message.text.split()
            if len(select_info) == 3:
                if int(select_info[1]):
                    select_user_id = int(select_info[1])
                    if(not db.check_user(select_user_id)):
                        await message.answer(cfg.error_not_found_user)
                    elif db.check_user(select_user_id):
                        if int(select_info[2]):
                            select_user_id = int(select_info[1])
                            select_add_balance = int(select_info[2])
                            db.addbalance(select_user_id, select_add_balance)
                            await message.answer(cfg.addbalance_right_admin(fnc.nick_with_link("пользователю", select_user_id), select_add_balance))
                            await dp.bot.send_message(select_user_id, cfg.addbalance_right_polz(select_add_balance))
                    else:
                        await message.answer(cfg.addbalance_command_error)
                else:
                    await message.answer(cfg.addbalance_command_error)
            else:
                await message.answer(cfg.addbalance_command_error)
        else:
            await message.answer(cfg.error_adm_dostup)

@dp.message_handler(commands=['rembalance'])
async def rembalance_user(message: types.Message):
    if message.chat.type == types.ChatType.PRIVATE:
        user_id = message.from_user.id
        if db.select_admin(user_id) > 0:
            select_info = message.text.split()
            if len(select_info) == 3:
                if int(select_info[1]):
                    select_user_id = int(select_info[1])
                    if(not db.check_user(select_user_id)):
                        await message.answer(cfg.error_not_found_user)
                    elif db.check_user(select_user_id):
                        if int(select_info[2]):
                            select_user_id = int(select_info[1])
                            select_add_balance = int(select_info[2])
                            db.rembalance(select_user_id, select_add_balance)
                            await message.answer(cfg.rembalance_right_admin(fnc.nick_with_link("пользователю", select_user_id), select_add_balance))
                            await dp.bot.send_message(select_user_id, cfg.rembalance_right_polz(select_add_balance))
                    else:
                        await message.answer(cfg.rembalance_command_error)
                else:
                    await message.answer(cfg.rembalance_command_error)
            else:
                await message.answer(cfg.rembalance_command_error)
        else:
            await message.answer(cfg.error_adm_dostup)


@dp.callback_query_handler()
async def buttons_callback(callback_query: types.CallbackQuery):
    if callback_query.data == "tariff_selection":
        markup_inline = types.InlineKeyboardMarkup(row_width=1)
        btn_inline1 = types.InlineKeyboardButton(cfg.start_tariff_button, callback_data='start_tariff')
        btn_inline2 = types.InlineKeyboardButton(cfg.standart_tariff_button, callback_data='standart_tariff')
        btn_inline3 = types.InlineKeyboardButton(cfg.premium_tariff_button, callback_data='premium_tariff')
        btn_inline4 = types.InlineKeyboardButton(cfg.my_profile, callback_data='profile_tariff')
        btn_inline5 = types.InlineKeyboardButton(cfg.support, callback_data='support_tariff')
        btn_inline6 = types.InlineKeyboardButton(cfg.back_button, callback_data='back_tariff')
        markup_inline.add(btn_inline1, btn_inline2, btn_inline3)
        markup_inline.row(btn_inline4, btn_inline5)
        markup_inline.add(btn_inline6)
        await callback_query.message.edit_caption(caption=cfg.tariff_list, reply_markup=markup_inline)
        await callback_query.answer(cfg.tariff_list_text)
    elif callback_query.data == "back_tariff" or callback_query.data == "profile_tariff":
        user_id = callback_query.from_user.id
        markup_inline = types.InlineKeyboardMarkup(row_width=1)
        btn_inline1 = types.InlineKeyboardButton(cfg.up_balance, callback_data='up_balance')
        btn_inline2 = types.InlineKeyboardButton(cfg.tariff_selection, callback_data='tariff_selection')
        markup_inline.add(btn_inline1, btn_inline2)
        await callback_query.message.edit_caption(caption=cfg.profile(user_id, db.select_balance(user_id), db.select_tariffe(user_id)), reply_markup=markup_inline)
        await callback_query.answer(cfg.back_text)
    elif callback_query.data == "support_tariff":
        markup_inline = types.InlineKeyboardMarkup(row_width=1)
        btn_inline1 = types.InlineKeyboardButton(cfg.support, callback_data='support', url="tg://user?id=1076482828")
        btn_inline2 = types.InlineKeyboardButton(cfg.back_button, callback_data='back_support')
        markup_inline.add(btn_inline1, btn_inline2)
        await callback_query.message.edit_caption("При индивидуальных запросах или возникновение трудностей, обратитесь по контакту ниже", reply_markup=markup_inline)
        await callback_query.answer(cfg.support_correct_text)
    elif callback_query.data == "back_support":
        markup_inline = types.InlineKeyboardMarkup(row_width=1)
        btn_inline1 = types.InlineKeyboardButton(cfg.start_tariff_button, callback_data='start_tariff')
        btn_inline2 = types.InlineKeyboardButton(cfg.standart_tariff_button, callback_data='standart_tariff')
        btn_inline3 = types.InlineKeyboardButton(cfg.premium_tariff_button, callback_data='premium_tariff')
        btn_inline4 = types.InlineKeyboardButton(cfg.my_profile, callback_data='profile_tariff')
        btn_inline5 = types.InlineKeyboardButton(cfg.support, callback_data='support_tariff')
        btn_inline6 = types.InlineKeyboardButton(cfg.back_button, callback_data='back_tariff')
        markup_inline.add(btn_inline1, btn_inline2, btn_inline3)
        markup_inline.row(btn_inline4, btn_inline5)
        markup_inline.add(btn_inline6)
        await callback_query.message.edit_caption(caption=cfg.tariff_list, reply_markup=markup_inline)
        await callback_query.answer(cfg.tariff_list_text)


@dp.message_handler()
async def other(message: types.Message):
    if message.chat.type == types.ChatType.PRIVATE:
        if message.text == cfg.my_profile:
            await profile(message)
        elif message.text == cfg.support:
            await supports_send(message)
        elif message.text == cfg.parser:
            await parsers_send(message)
        elif message.text == cfg.autoposting:
            await autoposting_send(message)

if __name__ == "__main__":
    executor.start_polling(dp)