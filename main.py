from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.storage import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from datbas import Data
from datetime import datetime
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError
import functions as fnc
import asyncio
import config as cfg
import logging
import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(cfg.TOKEN, parse_mode=types.ParseMode.MARKDOWN)
dp = Dispatcher(bot, storage=MemoryStorage())
db = Data("192.168.1.37", "5432", "pars_db", "pars_user", "pars_pwd")


telethon_client = TelegramClient(StringSession(cfg.STRING_SESSION), cfg.API_ID, cfg.API_HASH)


async def check_for_new_groups(current_count):
    new_count = len(db.select_all_channels_group())
    return new_count != current_count

async def search_and_forward():
    num = 0
    last_message_ids = {}
    messages_sent = {}

    await telethon_client.start()
    groups_count = len(db.select_all_channels_group())

    while True:
        try:
            groups = db.select_all_channels_group()
            if not groups:
                await asyncio.sleep(10)
                continue

            if await check_for_new_groups(groups_count):
                groups_count = len(groups)
                num = 0

            group = groups[num]
            user_id, chat_ids, keywords = group[0], group[2], group[5]

            for chat_id in chat_ids:
                last_id = last_message_ids.get(chat_id, 0)
                messages_to_check = 10
                forced_check = num == 0 or last_id == 0

                try:
                    async for message in telethon_client.iter_messages(chat_id, offset_id=last_id - messages_to_check, limit=messages_to_check, reverse=True):
                        if message.text and any(keyword.lower() in message.text.lower() for keyword in keywords):
                            message_key = (user_id, message.id)
                            if message_key not in messages_sent or forced_check:
                                await bot.send_message(user_id, message.text)
                                print(f"Message sent to user {user_id}: {message.text}")
                                messages_sent[message_key] = True

                except FloodWaitError as e:
                    wait_time = e.seconds
                    print(f"Flood wait error on chat {chat_id}. Sleeping for {wait_time} seconds.")
                    await asyncio.sleep(wait_time)
                finally:
                    messages = await telethon_client.get_messages(chat_id, limit=1)
                    if messages:
                        last_message_ids[chat_id] = messages[0].id

            num += 1
            if num >= len(groups):
                num = 0

        except Exception as e:
            print(f"Произошла ошибка: {e}")
            await asyncio.sleep(10)

        await asyncio.sleep(20)


class Create_group(StatesGroup):
    create_group_1 = State()
    create_group_2 = State()
    create_group_3 = State()

class Parsers_use(StatesGroup):
    parsers_use_1 = State()

async def profile(message):
    user_id = message.from_user.id
    markup_inline = types.InlineKeyboardMarkup(row_width=1, )
    btn_inline1 = types.InlineKeyboardButton(cfg.up_balance, callback_data='up_balance')
    markup_inline.add(btn_inline1)
    await message.answer_photo(photo=types.InputFile("img/testphoto.png"), caption=cfg.profile(user_id, db.select_balance(user_id)), reply_markup=markup_inline)

async def supports_send(message):
    markup_inline = types.InlineKeyboardMarkup(row_width=1)
    btn_inline1 = types.InlineKeyboardButton(cfg.support, callback_data='support', url="tg://user?id=1076482828")
    markup_inline.add(btn_inline1)
    await message.answer("При индивидуальных запросах или возникновение трудностей, обратитесь по контакту ниже", reply_markup=markup_inline)

async def parsers_send(message):
    markup_inline = types.InlineKeyboardMarkup(row_width=1)
    user_id = message.from_user.id
    group_names = db.select_group_name(user_id)
    max_buttons = 5
    for i in range(min(max_buttons, len(group_names))):
        button = types.InlineKeyboardButton(text=group_names[i], callback_data=group_names[i])
        markup_inline.add(button)

    btn_inline1 = types.InlineKeyboardButton(cfg.groups_add_button, callback_data='groups_add_button')
    markup_inline.add(btn_inline1)
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



#Функционал открытых inline кнопок
@dp.callback_query_handler()
async def buttons_callback(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.message.chat.type == types.ChatType.PRIVATE:
        user_id = callback_query.from_user.id
        if callback_query.data == "groups_add_button":
            number_group = db.check_number_group(user_id)
            if int(number_group) < 5:
                markup_reply = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
                markup_reply.add(cfg.cancel_creategroup)
                await Create_group.create_group_1.set()
                await callback_query.message.answer(cfg.create_group_text_1)
                await callback_query.message.answer(cfg.create_group_text_2, reply_markup=markup_reply)
                await callback_query.answer(cfg.create_group_button_uved)
            else:
                await callback_query.answer(cfg.error_group_5, show_alert=True)
        elif callback_query.data in db.select_group_name(user_id):
            await Parsers_use.parsers_use_1.set()
            number_group = db.select_number_group(user_id, callback_query.data)
            await state.update_data(number_group=number_group)
            channels = db.select_channels(user_id, callback_query.data)
            off_channels = db.select_all_off_channels(user_id, callback_query.data)
            markup_inline = types.InlineKeyboardMarkup(row_width=4)
            if db.check_date_tarife(user_id, callback_query.data) is None:
                for channel in channels:
                    buttons = types.InlineKeyboardButton(text=f"{channel} ⚠️", callback_data=f"{channel} ⚠️")
                    markup_inline.row(buttons)
                pay_money_buttons = types.InlineKeyboardButton(text=cfg.pay_money_channels, callback_data='pay_money_channels')
                markup_inline.add(pay_money_buttons)
            else:
                for channel in channels:
                    buttons = types.InlineKeyboardButton(text=f"{channel} ✅", callback_data=f"{channel} ✅")
                    markup_inline.row(buttons)
                for off_channel in off_channels:
                    buttons = types.InlineKeyboardButton(text=f"{off_channel} ❌", callback_data=f"{off_channel} ❌")
                    markup_inline.row(buttons)
            back_channels = types.InlineKeyboardButton(text=cfg.back_channels, callback_data='back_channels')
            markup_inline.add(back_channels)
            await callback_query.message.edit_caption(caption="TESTING", reply_markup=markup_inline)
        elif callback_query.data == "menu_after_pay":
            markup_inline = types.InlineKeyboardMarkup(row_width=1)
            user_id = callback_query.from_user.id
            group_names = db.select_group_name(user_id)
            max_buttons = 5
            for i in range(min(max_buttons, len(group_names))):
                button = types.InlineKeyboardButton(text=group_names[i], callback_data=group_names[i])
                markup_inline.add(button)

            btn_inline1 = types.InlineKeyboardButton(cfg.groups_add_button, callback_data='groups_add_button')
            markup_inline.add(btn_inline1)
            await callback_query.message.answer_photo(photo=types.InputFile("img/testphoto.png"), caption=cfg.parser_text, reply_markup=markup_inline)


@dp.callback_query_handler(state=Parsers_use.parsers_use_1)
async def parsers_use_1_button(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.message.chat.type == types.ChatType.PRIVATE:
        user_id = callback_query.from_user.id
        data = await state.get_data()
        number_group = data.get('number_group')
        channels = db.select_channels_with_number(number_group)
        check_tarife = db.check_date_tarife_for_number(user_id, number_group)
        group_name = db.select_group_name_for_number_group(user_id, number_group)
        if callback_query.data[:-2] in channels:
            if check_tarife is None:
                await callback_query.answer(text=cfg.error_oplata, show_alert=True)
            else:
                current_data = datetime.datetime.now()
                formated_check_date_tarife = datetime.datetime.strptime(check_tarife, "%Y-%m-%d %H:%M:%S")
                if current_data >= formated_check_date_tarife:
                    db.delete_old_tariffe(user_id, number_group)
                    await callback_query.answer(text=cfg.error_oplata, show_alert=True)
                else:
                    channel_name = callback_query.data
                    if channel_name[-1] == "✅":
                        channel_name = channel_name[:-1].strip()
                        all_channels = db.select_channels_number_group(number_group)
                        all_channels.remove(channel_name)
                        off_channels = db.select_off_channels(number_group)
                        off_channels.append(channel_name)
                        db.update_all_channels(number_group, all_channels)
                        db.update_off_channels(number_group, off_channels)
                        await state.update_data(number_group=number_group)
                        channels = db.select_channels_with_number(number_group)
                        markup_inline = types.InlineKeyboardMarkup(row_width=4)
                        for channel in channels:
                            buttons = types.InlineKeyboardButton(text=f"{channel} ✅", callback_data=f"{channel} ✅")
                            markup_inline.row(buttons)
                        for off_channel in off_channels:
                            buttons = types.InlineKeyboardButton(text=f"{off_channel} ❌", callback_data=f"{off_channel} ❌")
                            markup_inline.row(buttons)
                        back_channels = types.InlineKeyboardButton(text=cfg.back_channels, callback_data='back_channels')
                        markup_inline.add(back_channels)
                        await callback_query.message.edit_caption(caption="TESTING", reply_markup=markup_inline)
                    elif channel_name[-1] == "❌":
                        channel_name = channel_name[:-1].strip()
                        off_channels = db.select_off_channels(number_group)
                        off_channels.remove(channel_name)
                        all_channels = db.select_channels_number_group(number_group)
                        all_channels.append(channel_name)
                        db.update_all_channels(number_group, all_channels)
                        db.update_off_channels(number_group, off_channels)
                        await state.update_data(number_group=number_group)
                        channels = db.select_channels_with_number(number_group)
                        markup_inline = types.InlineKeyboardMarkup(row_width=4)
                        for channel in channels:
                            buttons = types.InlineKeyboardButton(text=f"{channel} ✅", callback_data=f"{channel} ✅")
                            markup_inline.row(buttons)
                        for off_channel in off_channels:
                            buttons = types.InlineKeyboardButton(text=f"{off_channel} ❌", callback_data=f"{off_channel} ❌")
                            markup_inline.row(buttons)
                        back_channels = types.InlineKeyboardButton(text=cfg.back_channels, callback_data='back_channels')
                        markup_inline.add(back_channels)
                        await callback_query.message.edit_caption(caption="TESTING", reply_markup=markup_inline)
        elif callback_query.data == "back_channels":
            await state.reset_state()
            markup_inline = types.InlineKeyboardMarkup(row_width=1)
            group_names = db.select_group_name(user_id)
            max_buttons = 5
            for i in range(min(max_buttons, len(group_names))):
                button = types.InlineKeyboardButton(text=group_names[i], callback_data=group_names[i])
                markup_inline.add(button)

            btn_inline1 = types.InlineKeyboardButton(cfg.groups_add_button, callback_data='groups_add_button')
            markup_inline.add(btn_inline1)
            await callback_query.message.edit_caption(caption=cfg.parser_text, reply_markup=markup_inline)
            await callback_query.answer(cfg.back_text)
        elif callback_query.data == "pay_money_channels":
            markup_inline = types.InlineKeyboardMarkup(row_width=1)
            btn_inline1 = types.InlineKeyboardButton(cfg.confirm_oplata, callback_data='confirm_oplata')
            btn_inline2 = types.InlineKeyboardButton(cfg.back_button, callback_data='back_oplata')
            markup_inline.add(btn_inline1, btn_inline2)
            channels_len = len(channels)
            money_oplata = str(5 * int(channels_len))
            await callback_query.message.edit_caption(caption=cfg.oplata_chatov(channels_len, money_oplata), reply_markup=markup_inline)
            await callback_query.answer(cfg.button_correct)
        elif callback_query.data == "confirm_oplata":
            balance = db.check_balance(user_id)
            channels_len = len(channels)
            money_oplata = 5 * int(channels_len)
            if balance >= money_oplata:
                db.update_balance(user_id, money_oplata)
                channels_len = len(channels)
                current_data = datetime.datetime.now()
                new_date = current_data + datetime.timedelta(days=30)
                formatted_date_new = new_date.strftime("%Y-%m-%d %H:%M:%S")
                db.add_date_tariffe(user_id, formatted_date_new, number_group)
                markup_inline = types.InlineKeyboardMarkup(row_width=1)
                btn_inline1 = types.InlineKeyboardButton(cfg.menu_button, callback_data='menu_after_pay')
                markup_inline.add(btn_inline1)
                await state.finish()
                await callback_query.message.delete()
                await callback_query.message.answer(text=cfg.tariffe_correct(group_name, channels_len, formatted_date_new), reply_markup=markup_inline)
            else:
                await callback_query.answer(text=cfg.tariffe_error, show_alert=True)
        elif callback_query.data == "back_oplata":
            channels = db.select_channels_for_number(user_id, number_group)
            markup_inline = types.InlineKeyboardMarkup(row_width=4)
            for channel in channels:
                buttons = types.InlineKeyboardButton(text=channel, callback_data=channel)
                markup_inline.row(buttons)
            if db.check_date_tarife_for_number(user_id, number_group) is None:
                pay_money_buttons = types.InlineKeyboardButton(text=cfg.pay_money_channels, callback_data='pay_money_channels')
                markup_inline.add(pay_money_buttons)
            back_channels = types.InlineKeyboardButton(text=cfg.back_channels, callback_data='back_channels')
            markup_inline.add(back_channels)
            await callback_query.message.edit_caption(caption="TESTING", reply_markup=markup_inline)
        elif callback_query.data == "back_sostoyanie":
            markup_inline = types.InlineKeyboardMarkup(row_width=1)
            user_id = callback_query.from_user.id
            group_names = db.select_group_name(user_id)
            max_buttons = 5
            for i in range(min(max_buttons, len(group_names))):
                button = types.InlineKeyboardButton(text=group_names[i], callback_data=group_names[i])
                markup_inline.add(button)

            btn_inline1 = types.InlineKeyboardButton(cfg.groups_add_button, callback_data='groups_add_button')
            markup_inline.add(btn_inline1)
            await callback_query.message.answer_photo(photo=types.InputFile("img/testphoto.png"), caption=cfg.parser_text, reply_markup=markup_inline)
            await state.reset_state()


@dp.message_handler(state=Parsers_use.parsers_use_1)
async def parsers_use_1_text(message: types.Message, state: FSMContext):
    if message.chat.type == types.ChatType.PRIVATE:
        if message.text == "/cancel":
            await message.answer(cfg.cancel_sostoyanie)
            await state.reset_state()
        else:
            markup_inline = types.InlineKeyboardMarkup(row_width=1)
            btn1_inline = types.InlineKeyboardButton(cfg.back_button, callback_data="back_sostoyanie")
            markup_inline.add(btn1_inline)
            await message.answer(cfg.error_parsers_texts, reply_markup=markup_inline)


@dp.message_handler(state=Create_group.create_group_1)
async def create_group_func_1(message: types.Message, state: FSMContext):
    if message.chat.type == types.ChatType.PRIVATE:
        user_id = message.from_user.id
        if message.text == cfg.cancel_creategroup:
            markup_reply = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
            markup_reply.add(cfg.autoposting)
            markup_reply.add(cfg.parser)
            markup_reply.row(cfg.my_profile, cfg.support)
            await state.reset_state()
            await message.answer(cfg.cancel_creategroup_text, reply_markup=markup_reply)
        elif message.text:
            if 3 <= len(message.text) <= 15:
                if message.text in db.select_group_name(user_id):
                    await message.answer(cfg.error_name_again)
                else:
                    await state.update_data(group_name=message.text)
                    await message.answer(cfg.create_group_text_3)
                    await Create_group.create_group_2.set()
            else:
                await message.answer(cfg.error_len_name_group)

@dp.callback_query_handler(state=Create_group.create_group_1)
async def button_group_1(callback_query: types.CallbackQuery):
    if callback_query.data is not None:
        await callback_query.answer(cfg.error_button_create_group)

@dp.message_handler(state=Create_group.create_group_2)
async def create_group_func_2(message: types.Message, state: FSMContext):
    if message.chat.type == types.ChatType.PRIVATE:
        user_id = message.from_user.id
        textsing = message.text
        text_lines = textsing.strip().split('\n')
        if message.text == cfg.cancel_creategroup:
            markup_reply = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
            markup_reply.add(cfg.autoposting)
            markup_reply.add(cfg.parser)
            markup_reply.row(cfg.my_profile, cfg.support)
            await state.reset_state()
            await message.answer(cfg.cancel_creategroup_text, reply_markup=markup_reply)
        elif message.text:
            if 2 <= len(message.text) <= 500:
                if 1 <= len(text_lines) <= 20:
                    try:
                        await state.update_data(text_lines=text_lines)
                        await message.answer(cfg.create_group_text_4)
                        await Create_group.create_group_3.set()
                    except Exception as es:
                        await state.reset_state()
                        markup_reply = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
                        markup_reply.add(cfg.autoposting)
                        markup_reply.add(cfg.parser)
                        markup_reply.row(cfg.my_profile, cfg.support)
                        await message.answer(cfg.error_create_group, reply_markup=markup_reply)
                        print(f"[ERROR] {es}")
                else:
                    await message.answer(cfg.error_len_keyword_create)
            else:
                await message.answer(cfg.error_len_keyword)

@dp.callback_query_handler(state=Create_group.create_group_2)
async def button_group_2(callback_query: types.CallbackQuery):
    if callback_query.data is not None:
        await callback_query.answer(cfg.error_button_create_group)

@dp.message_handler(state=Create_group.create_group_3)
async def create_group_func_3(message: types.Message, state: FSMContext):
    if message.chat.type == types.ChatType.PRIVATE:
        user_id = message.from_user.id
        textsing = message.text
        text_lines = textsing.strip().split('\n')
        if message.text == cfg.cancel_creategroup:
            markup_reply = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
            markup_reply.add(cfg.autoposting)
            markup_reply.add(cfg.parser)
            markup_reply.row(cfg.my_profile, cfg.support)
            await state.reset_state()
            await message.answer(cfg.cancel_creategroup_text, reply_markup=markup_reply)
        elif message.text:
            if 2 <= len(message.text) <= 1000:
                if 10 <= len(text_lines) <= 50:
                    try:
                        check_number_group = db.check_numbers_group()
                        new_number_group = check_number_group + 1
                        data = await state.get_data()
                        cashe_group_name = data.get('group_name')
                        cashe_keyword = data.get('text_lines')
                        db.add_channels(user_id, new_number_group, cashe_keyword, text_lines, cashe_group_name)
                        markup_reply = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
                        markup_reply.add(cfg.autoposting)
                        markup_reply.add(cfg.parser)
                        markup_reply.row(cfg.my_profile, cfg.support)
                        await message.answer(cfg.right_create_group, reply_markup=markup_reply)
                        await state.finish()
                    except Exception as es:
                        await state.reset_state()
                        markup_reply = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
                        markup_reply.add(cfg.autoposting)
                        markup_reply.add(cfg.parser)
                        markup_reply.row(cfg.my_profile, cfg.support)
                        await message.answer(cfg.error_create_group, reply_markup=markup_reply)
                        print(f"[ERROR] {es}")
                else:
                    await message.answer(cfg.error_len_channels_create)
            else:
                await message.answer(cfg.error_len_channels)

@dp.callback_query_handler(state=Create_group.create_group_3)
async def button_group_2(callback_query: types.CallbackQuery):
    if callback_query.data is not None:
        await callback_query.answer(cfg.error_button_create_group)

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


async def on_startup(_):
    asyncio.create_task(search_and_forward())

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)