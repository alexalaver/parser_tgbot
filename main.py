from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.storage import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from datbas import Data
from datetime import datetime, timedelta
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError, ChannelPrivateError, ChatForbiddenError, UserPrivacyRestrictedError, PeerIdInvalidError, SessionPasswordNeededError, PhoneCodeExpiredError, PhoneNumberUnoccupiedError, RPCError
import functions as fnc
import asyncio
import config as cfg
import logging
import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(cfg.TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())
db = Data("192.168.1.37", "5432", "pars_db", "pars_user", "pars_pwd")

# with TelegramClient(StringSession(), cfg.API_ID, cfg.API_HASH) as client:
#     print("String Session:", client.session.save())

client = TelegramClient(StringSession(), cfg.API_ID, cfg.API_HASH)
telethon_client = TelegramClient(StringSession(cfg.STRING_SESSION), cfg.API_ID, cfg.API_HASH)

async def check_for_new_groups(current_count):
    new_count = len(db.select_all_channels_group())
    return new_count != current_count

async def check_for_new_autoposting_groups(current_count):
    new_count = len(db.select_all_channels_autoposting_group())
    return new_count != current_count

async def check_for_new_channels(current_count):
    new_count = len(db.select_all_channels_group())
    return new_count != current_count

async def check_private_channel(channels, user_id, number_group):
    channels_link = [item for item in channels if len(item) >= 13 and item[13] == '+']
    if channels_link is None:
        pass
    else:
        await bot.send_message(cfg.admin_id, f"{fnc.nick_with_link('Пользователь', user_id)}, добавил закрытые чаты, вам необходимо подписаться на них.\n\n{channels_link}\n\nНомер группы - {str(number_group)}", parse_mode=types.ParseMode.MARKDOWN)

async def check_keywords_len(keywords, num):
    groups = db.select_all_channels_group()
    group = groups[num]
    old_keywords = group[5]
    result = all(item in keywords for item in old_keywords)
    if result:
        return True
    else:
        return False


async def search_and_forward():
    num = 0
    last_message_ids = {}

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
            chat_ids = [item for item in chat_ids if item.endswith('✅')]
            chat_ids = [item for item in chat_ids if len(item) < 13 or item[13] != '+']
            if await check_for_new_channels(len(chat_ids)):
                groups = db.select_all_channels_group()
                group = groups[num]
                user_id, chat_ids, keywords = group[0], group[2], group[5]
                chat_ids = [item for item in chat_ids if item.endswith('✅')]
                chat_ids = [item for item in chat_ids if len(item) < 13 or item[13] != '+']

            number_group = group[1]

            for chat_id in chat_ids:
                trimmed_chat_id = chat_id[:-2]
                exception_occurred = False
                messages_sent = db.select_message_id(number_group)
                try:
                    chat_select_id = await telethon_client.get_entity(trimmed_chat_id)
                    chat_check_id = chat_select_id.id
                    last_id = last_message_ids.get(trimmed_chat_id, 0)
                    messages_to_check = 30
                    forced_check = num == 0 and last_id == 0
                    async for message in telethon_client.iter_messages(chat_check_id, offset_id=last_id - messages_to_check, limit=messages_to_check, reverse=True):
                        if message.text:
                            for keyword in keywords:
                                if keyword.lower() in message.text.lower():
                                    message_key = [chat_check_id, message.id]
                                    if message_key not in messages_sent:
                                        sender = await message.get_sender()
                                        if "http" in trimmed_chat_id:
                                            link_message = f"{trimmed_chat_id}/{str(message.id)}"
                                        else:
                                            link_message = f"t.me/{trimmed_chat_id[1:]}/{str(message.id)}"
                                        sender_identifier = f"@{sender.username}" if sender else "Анонимный пользователь"
                                        message_text = f"Обнаружено ключевое слово\n\nЧат: {trimmed_chat_id}\n\nПользователь: {sender_identifier}\n\nЗапрос: {keyword}\n\nСсылка на сообщение: {link_message}\n\nТекст:\n{message.text}"
                                        await bot.send_message(user_id, message_text)
                                        # print(f"Message sent to user {user_id}: {message.text}")
                                        db.update_all_message_ids(number_group, message_key)
                                        await asyncio.sleep(2)
                                    break

                except FloodWaitError as e:
                    wait_time = e.seconds
                    print(f"Flood wait error on chat {trimmed_chat_id}. Sleeping for {wait_time} seconds.")
                    await asyncio.sleep(3)
                    exception_occurred = True
                except Exception as erri:
                    print(f"[ERROR EXCEPTION] {erri}")
                    all_channels = db.select_channels_with_number(number_group)
                    new_callback = chat_id[:-1] + '⏳'
                    new_channels = [new_callback if item == chat_id else item for item in all_channels]
                    db.update_all_channels(number_group, new_channels)
                    await asyncio.sleep(2)
                    exception_occurred = True
                finally:
                    if exception_occurred is False:
                        messages = await telethon_client.get_messages(trimmed_chat_id, limit=1)
                        if messages:
                            last_message_ids[trimmed_chat_id] = messages[0].id
                        else:
                            pass

            num += 1
            if num >= len(groups):
                num = 0

        except Exception as e:
            print(f"Произошла ошибка: {e}")
            await asyncio.sleep(10)

        await asyncio.sleep(5)


async def search_and_forward_close_group():
    num = 0
    last_message_ids = {}

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
            user_id, chat_ids, keywords, channels_link = group[0], group[7], group[5], group[2]
            channels_link = [item for item in channels_link if len(item) >= 13 and item[13] == '+']
            if await check_for_new_channels(len(channels_link)):
                groups = db.select_all_channels_group()
                group = groups[num]
                user_id, chat_ids, keywords, channels_link = group[0], group[7], group[5], group[2]
                channels_link = [item for item in channels_link if len(item) >= 13 and item[13] == '+']
            number_group = group[1]
            if chat_ids is not None:
                for chat_id in chat_ids:
                    index_chat_id = int(chat_id[0])
                    links_1 = channels_link[index_chat_id - 1]
                    links_2 = links_1[-1]
                    if links_2 == "✅":
                        trimmed_chat_ids = int(chat_id[3:])
                        exception_occurred = False
                        messages_sent = db.select_message_id(number_group)
                        try:
                            last_id = last_message_ids.get(trimmed_chat_ids, 0)
                            messages_to_check = 30
                            forced_check = num == 0 and last_id == 0
                            async for message in telethon_client.iter_messages(trimmed_chat_ids, offset_id=last_id - messages_to_check, limit=messages_to_check, reverse=True):
                                if message.text:
                                    for keyword in keywords:
                                        if keyword.lower() in message.text.lower():
                                            message_key = [trimmed_chat_ids, message.id]
                                            if message_key not in messages_sent:
                                                sender = await message.get_sender()
                                                sender_identifier = f"@{sender.username}" if sender else "Анонимный пользователь"
                                                message_text = f"Обнаружено ключевое слово\n\nЧат: {links_1[:-2]}\n\nПользователь: {sender_identifier}\n\nЗапрос: {keyword}\n\nСсылка на сообщение: Чат закрыт.\n\nТекст:\n{message.text}"
                                                await bot.send_message(user_id, message_text)
                                                # print(f"Message sent to user {user_id}: {message.text}")
                                                db.update_all_message_ids(number_group, message_key)
                                                await asyncio.sleep(2)
                                            break

                        except FloodWaitError as e:
                            print(f"Flood wait error on chat. Sleeping for seconds. {e}")
                            await asyncio.sleep(2)
                            exception_occurred = True
                        except ChannelPrivateError:
                            print("Ошибка доступа: канал закрыт и у меня нет к нему доступа.")
                            await asyncio.sleep(2)
                            exception_occurred = True
                        except ChatForbiddenError:
                            print("Ошибка доступа: я исключён из чата или покинул его.")
                            await asyncio.sleep(2)
                            exception_occurred = True
                        except UserPrivacyRestrictedError:
                            print("Ошибка доступа: ограничения конфиденциальности пользователя.")
                            await asyncio.sleep(2)
                            exception_occurred = True
                        except PeerIdInvalidError:
                            print("Ошибка ID: не найден ID")
                            await asyncio.sleep(2)
                            exception_occurred = True
                        except ValueError:
                            print("Ошибка ID: не найден ID")
                            await asyncio.sleep(2)
                            exception_occurred = True
                        except Exception as e:
                            print(f"Произошла непредвиденная ошибка: {type(e).__name__}, {e}")
                            await asyncio.sleep(2)
                            exception_occurred = True
                        finally:
                            if exception_occurred is False:
                                messages = await telethon_client.get_messages(trimmed_chat_ids, limit=1)
                                if messages:
                                    last_message_ids[trimmed_chat_ids] = messages[0].id
                                    await asyncio.sleep(2)
                                else:
                                    pass
                        await asyncio.sleep(1)
            num += 1
            if num >= len(groups):
                num = 0

        except Exception as e:
            print(f"Произошла ошибка: {type(e).__name__}")
            await asyncio.sleep(2)

        await asyncio.sleep(1)

async def autoposting_forward():
    num = 0

    groups_count = len(db.select_all_channels_autoposting_group())

    while True:
        try:
            groups = db.select_all_channels_autoposting_group()
            if not groups:
                await asyncio.sleep(10)
                continue

            if await check_for_new_autoposting_groups(groups_count):
                groups_count = len(groups)
                num = 0

            group = groups[num]
            user_id, chat_ids, string_session, message_id, time_betw, date_betw, number_group = group[0], group[4], group[3], group[7], group[8], group[9], group[1]

            async with TelegramClient(StringSession(string_session), cfg.API_ID, cfg.API_HASH) as telethon_client_autoposting:
                current_date = datetime.datetime.now()
                formated_base = datetime.datetime.strptime(date_betw, "%Y-%m-%d %H:%M:%S")

                if current_date > formated_base:
                    for chat_id in chat_ids:
                        try:
                            await telethon_client_autoposting.forward_messages(entity=chat_id, messages=int(message_id), from_peer="@parsersi_bot")
                            await bot.send_message(f"Рекламный пост, успешно отправлен в чат {chat_id}")
                            await asyncio.sleep(5)
                        except RPCError as err:
                            print(f"[ERROR RPCError] {err}")
                        except Exception as erri:
                            print(f"[ERROR EXCEPTION] {erri}")

                else:
                    time_in_60_minutes = current_date + datetime.timedelta(minutes=int(time_betw))
                    db.update_date_betw(time_in_60_minutes, number_group)

            num += 1
            if num >= len(groups):
                num = 0

        except Exception as e:
            print(f"Произошла ошибка: {e}")

        await asyncio.sleep(1)

class Create_group(StatesGroup):
    create_group_1 = State()
    create_group_2 = State()
    create_group_3 = State()

class Create_account_autoposting(StatesGroup):
    create_autoposting_1 = State()
    create_autoposting_2 = State()

class Parsers_use(StatesGroup):
    parsers_use_1 = State()

class Account_use(StatesGroup):
    account_use_1 = State()

class Change_keyword(StatesGroup):
    change_keyword_1 = State()

class Add_chat_ids(StatesGroup):
    panel_adm = State()
    add_ids_1 = State()
    add_ids_2 = State()

class Accounts_button(StatesGroup):
    select_accounts_button = State()

class Parser_groups_button(StatesGroup):
    select_groups_button = State()

class Account_post_button(StatesGroup):
    account_post_button_1 = State()

class Add_post(StatesGroup):
    add_post_1 = State()
    add_post_2 = State()
    add_post_3 = State()

async def profile(message):
    user_id = message.from_user.id
    markup_inline = types.InlineKeyboardMarkup(row_width=1, )
    btn_inline1 = types.InlineKeyboardButton(cfg.up_balance, callback_data='up_balance')
    markup_inline.add(btn_inline1)
    await message.answer_photo(photo=types.InputFile("img/testphoto.png"), caption=cfg.profile(user_id, db.select_balance(user_id)), reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)

async def supports_send(message):
    markup_inline = types.InlineKeyboardMarkup(row_width=1)
    btn_inline1 = types.InlineKeyboardButton(cfg.support, callback_data='support', url=f"tg://user?id={cfg.admin_id}")
    markup_inline.add(btn_inline1)
    await message.answer("При индивидуальных запросах или возникновение трудностей, обратитесь по контакту ниже", reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)

async def parsers_send(message):
    markup_inline = types.InlineKeyboardMarkup(row_width=1)
    markup_inline.add(types.InlineKeyboardButton(cfg.groups_button, callback_data='groups_parser'))
    await message.answer_photo(photo=types.InputFile("img/testphoto.png"), caption=cfg.parser_groups_text, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)

async def autoposting_send(message):
    markup_inline = types.InlineKeyboardMarkup(row_width=1)
    btn_inline1 = types.InlineKeyboardButton(cfg.account_button, callback_data='accounts_button')
    markup_inline.add(btn_inline1)
    await message.answer_photo(photo=types.InputFile("img/testphoto.png"), caption=cfg.autoposting_text, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)

async def panel_administration(message):
    user_id = message.from_user.id
    if db.select_admin(user_id) > 0:
        markup_reply = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        markup_reply.add(cfg.add_chat_id_button, cfg.back_button)
        await message.answer(cfg.panel_admin_text, reply_markup=markup_reply, parse_mode=types.ParseMode.MARKDOWN)
        await Add_chat_ids.panel_adm.set()
    else:
        await message.answer(cfg.error_adm_dostup)


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
        if db.select_admin(user_id) > 0:
            markup_reply.add(cfg.admin_panel_button)

        await message.answer('test', reply_markup=markup_reply, parse_mode=types.ParseMode.MARKDOWN)
        await profile(message)

@dp.message_handler(commands=['addadmin'])
async def add_admin_user(message: types.Message):
    if message.chat.type == types.ChatType.PRIVATE:
        user_id = message.from_user.id
        if db.select_admin(user_id) > 0:
            select_adm_id = int(message.text.split()[1])
            if(not db.check_user(select_adm_id)):
                await message.answer(cfg.error_not_found_user, parse_mode=types.ParseMode.MARKDOWN)
            elif db.check_user(select_adm_id):
                db.add_admin(select_adm_id)
                await message.answer(cfg.right_add_admin(fnc.nick_with_link("администратора", select_adm_id)), parse_mode=types.ParseMode.MARKDOWN)
                await dp.bot.send_message(select_adm_id, cfg.take_adm, parse_mode=types.ParseMode.MARKDOWN)
            else:
                await message.answer(cfg.error_command, parse_mode=types.ParseMode.MARKDOWN)
        else:
            await message.answer(cfg.error_adm_dostup, parse_mode=types.ParseMode.MARKDOWN)


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
                        await message.answer(cfg.error_not_found_user, parse_mode=types.ParseMode.MARKDOWN)
                    elif db.check_user(select_adm_id):
                        balance_user = db.select_balance(select_adm_id)
                        await message.answer(cfg.balance_user_text(fnc.nick_with_link("пользователя", select_adm_id), str(balance_user)), parse_mode=types.ParseMode.MARKDOWN)
                else:
                    await message.answer(cfg.balance_command_error, parse_mode=types.ParseMode.MARKDOWN)
            else:
                await message.answer(cfg.error_command, parse_mode=types.ParseMode.MARKDOWN)
        else:
            await message.answer(cfg.error_adm_dostup, parse_mode=types.ParseMode.MARKDOWN)

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
                        await message.answer(cfg.error_not_found_user, parse_mode=types.ParseMode.MARKDOWN)
                    elif db.check_user(select_user_id):
                        if int(select_info[2]):
                            select_user_id = int(select_info[1])
                            select_add_balance = int(select_info[2])
                            db.addbalance(select_user_id, select_add_balance)
                            await message.answer(cfg.addbalance_right_admin(fnc.nick_with_link("пользователю", select_user_id), select_add_balance), parse_mode=types.ParseMode.MARKDOWN)
                            await dp.bot.send_message(select_user_id, cfg.addbalance_right_polz(select_add_balance), parse_mode=types.ParseMode.MARKDOWN)
                    else:
                        await message.answer(cfg.addbalance_command_error, parse_mode=types.ParseMode.MARKDOWN)
                else:
                    await message.answer(cfg.addbalance_command_error, parse_mode=types.ParseMode.MARKDOWN)
            else:
                await message.answer(cfg.addbalance_command_error, parse_mode=types.ParseMode.MARKDOWN)
        else:
            await message.answer(cfg.error_adm_dostup, parse_mode=types.ParseMode.MARKDOWN)

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
                        await message.answer(cfg.error_not_found_user, parse_mode=types.ParseMode.MARKDOWN)
                    elif db.check_user(select_user_id):
                        if int(select_info[2]):
                            select_user_id = int(select_info[1])
                            select_add_balance = int(select_info[2])
                            db.rembalance(select_user_id, select_add_balance)
                            await message.answer(cfg.rembalance_right_admin(fnc.nick_with_link("пользователю", select_user_id), select_add_balance), parse_mode=types.ParseMode.MARKDOWN)
                            await dp.bot.send_message(select_user_id, cfg.rembalance_right_polz(select_add_balance), parse_mode=types.ParseMode.MARKDOWN)
                    else:
                        await message.answer(cfg.rembalance_command_error, parse_mode=types.ParseMode.MARKDOWN)
                else:
                    await message.answer(cfg.rembalance_command_error, parse_mode=types.ParseMode.MARKDOWN)
            else:
                await message.answer(cfg.rembalance_command_error, parse_mode=types.ParseMode.MARKDOWN)
        else:
            await message.answer(cfg.error_adm_dostup, parse_mode=types.ParseMode.MARKDOWN)



#Функционал открытых inline кнопок
@dp.callback_query_handler()
async def buttons_callback(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.message.chat.type == types.ChatType.PRIVATE:
        user_id = callback_query.from_user.id
        if callback_query.data == "accounts_button":
            markup_inline = types.InlineKeyboardMarkup(row_width=1)
            user_id = callback_query.from_user.id
            group_names = db.select_autoposting_group_name(user_id)
            max_buttons = 5
            for i in range(min(max_buttons, len(group_names))):
                button = types.InlineKeyboardButton(text=group_names[i], callback_data=group_names[i])
                markup_inline.add(button)
            btn1_inline = types.InlineKeyboardButton(cfg.add_account_button, callback_data="add_account")
            btn2_inline = types.InlineKeyboardButton(cfg.back_button, callback_data="back_autoposting_menu")
            markup_inline.add(btn1_inline, btn2_inline)
            await callback_query.message.edit_caption(caption=cfg.account_menu_text, reply_markup=markup_inline)
            await Accounts_button.select_accounts_button.set()
        elif callback_query.data == "groups_parser":
            markup_inline = types.InlineKeyboardMarkup(row_width=1)
            group_names = db.select_group_name(user_id)
            max_buttons = 5
            for i in range(min(max_buttons, len(group_names))):
                button = types.InlineKeyboardButton(text=group_names[i], callback_data=group_names[i])
                markup_inline.add(button)

            btn_inline1 = types.InlineKeyboardButton(cfg.groups_add_button, callback_data='groups_add_button')
            btn_inline2 = types.InlineKeyboardButton(cfg.back_button, callback_data='back_groups_parser')
            markup_inline.add(btn_inline1, btn_inline2)
            await callback_query.message.edit_caption(cfg.parser_text, reply_markup=markup_inline)
            await Parser_groups_button.select_groups_button.set()
        elif callback_query.data == "menu_after_pay":
            markup_inline = types.InlineKeyboardMarkup(row_width=1)
            btn_inline1 = types.InlineKeyboardButton(cfg.groups_button, callback_data='groups_parser')
            markup_inline.add(btn_inline1)
            await callback_query.message.answer_photo(photo=types.InputFile("img/testphoto.png"), caption=cfg.parser_groups_text, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
        elif callback_query.data == "menu_after_pay_autoposting":
            markup_inline = types.InlineKeyboardMarkup(row_width=1)
            btn_inline1 = types.InlineKeyboardButton(cfg.account_button, callback_data='accounts_button')
            markup_inline.add(btn_inline1)
            await callback_query.message.answer_photo(photo=types.InputFile("img/testphoto.png"), caption=cfg.autoposting_text, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)

@dp.callback_query_handler(state=Parser_groups_button.select_groups_button)
async def parser_group_button(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.message.chat.type == types.ChatType.PRIVATE:
        user_id = callback_query.from_user.id
        if callback_query.data == "back_groups_parser":
            markup_inline = types.InlineKeyboardMarkup(row_width=1)
            markup_inline.add(types.InlineKeyboardButton(cfg.groups_button, callback_data='groups_parser'))
            await callback_query.message.edit_caption(caption=cfg.parser_groups_text, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
            await state.finish()
        elif callback_query.data == "groups_add_button":
            number_group = db.check_number_group(user_id)
            if int(number_group) < 5:
                markup_reply = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
                markup_reply.add(cfg.cancel_creategroup)
                await Create_group.create_group_1.set()
                await callback_query.message.answer(cfg.create_group_text_1, parse_mode=types.ParseMode.MARKDOWN)
                await callback_query.message.answer(cfg.create_group_text_2, reply_markup=markup_reply, parse_mode=types.ParseMode.MARKDOWN)
            else:
                await callback_query.answer(cfg.error_group_5, show_alert=True)
        elif callback_query.data in db.select_group_name(user_id):
            await Parsers_use.parsers_use_1.set()
            number_group = db.select_number_group(user_id, callback_query.data)
            await state.update_data(number_group=number_group)
            channels = db.select_channels(user_id, callback_query.data)
            markup_inline = types.InlineKeyboardMarkup(row_width=2)
            channels_count = len(channels)
            channels_page = fnc.get_category(channels_count)
            page_here = 1
            from_page = 0
            before_page = 10
            await state.update_data(channels_count=channels_count)
            await state.update_data(channels_page=channels_page)
            await state.update_data(page_here=page_here)
            await state.update_data(from_page=from_page)
            await state.update_data(before_page=before_page)
            for channel in channels[from_page:before_page]:
                buttons = types.InlineKeyboardButton(text=channel, callback_data=channel)
                markup_inline.row(buttons)
            buttons_count = types.InlineKeyboardButton(text=f"Страница {page_here}/{channels_page} 📄", callback_data="page")
            markup_inline.add(buttons_count)
            if channels_count > 10:
                buttons_next = types.InlineKeyboardButton(text=cfg.next_page, callback_data="next_page")
                buttons_old = types.InlineKeyboardButton(text=cfg.old_page, callback_data="old_page")
                markup_inline.row(buttons_old, buttons_next)
            if db.check_date_tarife(user_id, callback_query.data) is None:
                pay_money_buttons = types.InlineKeyboardButton(text=cfg.pay_money_channels, callback_data='pay_money_channels')
                markup_inline.add(pay_money_buttons)
            change_keywords = types.InlineKeyboardButton(text=cfg.change_keyword_button, callback_data='change_keyword')
            back_channels = types.InlineKeyboardButton(text=cfg.back_channels, callback_data='back_channels')
            markup_inline.add(change_keywords)
            markup_inline.add(back_channels)
            await callback_query.message.edit_caption(caption=cfg.group_text_use, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
        elif callback_query.data == "back_sostoyanie":
            markup_inline = types.InlineKeyboardMarkup(row_width=1)
            btn_inline1 = types.InlineKeyboardButton(cfg.groups_button, callback_data='groups_parser')
            markup_inline.add(btn_inline1)
            await callback_query.message.answer_photo(photo=types.InputFile("img/testphoto.png"), caption=cfg.parser_groups_text, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
            await state.reset_state()

@dp.message_handler(state=Parser_groups_button.select_groups_button)
async def parsers_groups_1_text(message: types.Message, state: FSMContext):
    if message.chat.type == types.ChatType.PRIVATE:
        if message.text == "/cancel":
            await message.answer(cfg.cancel_sostoyanie, parse_mode=types.ParseMode.MARKDOWN)
            await state.reset_state()
        else:
            markup_inline = types.InlineKeyboardMarkup(row_width=1)
            btn1_inline = types.InlineKeyboardButton(cfg.back_button, callback_data="back_sostoyanie")
            markup_inline.add(btn1_inline)
            await message.answer(cfg.error_parsers_texts, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)

@dp.callback_query_handler(state=Accounts_button.select_accounts_button)
async def accounts_button_1_button(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.message.chat.type == types.ChatType.PRIVATE:
        user_id = callback_query.from_user.id
        if callback_query.data == "back_autoposting_menu":
            markup_inline = types.InlineKeyboardMarkup(row_width=1)
            markup_inline.add(types.InlineKeyboardButton(cfg.account_button, callback_data='accounts_button'))
            await callback_query.message.edit_caption(caption=cfg.autoposting_text, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
            await state.finish()
        elif callback_query.data == "add_account":
            number_group = db.check_numbers_autoposting_group(user_id)
            if int(number_group) < 5:
                markup_reply = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
                markup_reply.add(cfg.cancel_creategroup)
                await Create_account_autoposting.create_autoposting_1.set()
                db.delete_sms_get(user_id)
                db.sms_get_add(user_id)
                await callback_query.message.answer(cfg.create_account_autoposting_1, parse_mode=types.ParseMode.MARKDOWN)
                await callback_query.message.answer(cfg.create_account_autoposting_2, reply_markup=markup_reply, parse_mode=types.ParseMode.MARKDOWN)
            else:
                await callback_query.answer(cfg.error_autoposting_group_5, show_alert=True)
        elif callback_query.data in db.select_account_name(user_id):
            number_account = str(db.select_account_number(user_id, callback_query.data))
            await state.update_data(number_account)
            markup_inline = types.InlineKeyboardMarkup(row_width=1)
            user_id = callback_query.from_user.id
            group_names = db.select_autoposting_post_name_for_number(user_id, number_account)
            max_buttons = 5
            for i in range(min(max_buttons, len(group_names))):
                button = types.InlineKeyboardButton(text=group_names[i], callback_data=group_names[i])
                markup_inline.add(button)
            btn1_inline = types.InlineKeyboardButton(cfg.add_post_button, callback_data="add_post")
            btn2_inline = types.InlineKeyboardButton(cfg.back_button, callback_data="back_autoposting_account")
            markup_inline.add(btn1_inline, btn2_inline)
            await callback_query.message.edit_caption(caption=cfg.post_text, reply_markup=markup_inline)
            await Account_post_button.account_post_button_1.set()
        elif callback_query.data == "back_sostoyanie":
            markup_inline = types.InlineKeyboardMarkup(row_width=1)
            btn_inline1 = types.InlineKeyboardButton(cfg.account_button, callback_data='accounts_button')
            markup_inline.add(btn_inline1)
            await callback_query.message.answer_photo(photo=types.InputFile("img/testphoto.png"), caption=cfg.autoposting_text, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
            await state.reset_state()

@dp.message_handler(state=Accounts_button.select_accounts_button)
async def accounts_button_1_text(message: types.Message, state: FSMContext):
    if message.chat.type == types.ChatType.PRIVATE:
        if message.text == "/cancel":
            await message.answer(cfg.cancel_sostoyanie, parse_mode=types.ParseMode.MARKDOWN)
            await state.reset_state()
        else:
            markup_inline = types.InlineKeyboardMarkup(row_width=1)
            btn1_inline = types.InlineKeyboardButton(cfg.back_button, callback_data="back_sostoyanie")
            markup_inline.add(btn1_inline)
            await message.answer(cfg.error_autoposting_texts, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)

@dp.callback_query_handler(state=Account_post_button.account_post_button_1)
async def Button_account_post(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.message.chat.type == types.ChatType.PRIVATE:
        user_id = callback_query.from_user.id
        if callback_query.data == "back_autoposting_account":
            markup_inline = types.InlineKeyboardMarkup(row_width=1)
            data = await state.get_data()
            number_account = data.get("number_account")
            user_id = callback_query.from_user.id
            group_names = db.select_autoposting_post_name_for_number(user_id, number_account)
            max_buttons = 5
            for i in range(min(max_buttons, len(group_names))):
                button = types.InlineKeyboardButton(text=group_names[i], callback_data=group_names[i])
                markup_inline.add(button)
            btn1_inline = types.InlineKeyboardButton(cfg.add_account_button, callback_data="add_account")
            btn2_inline = types.InlineKeyboardButton(cfg.back_button, callback_data="back_autoposting_menu")
            markup_inline.add(btn1_inline, btn2_inline)
            text = cfg.account_menu_text
            await callback_query.message.edit_caption(caption="аккаунты", reply_markup=markup_inline)
            await Accounts_button.select_accounts_button.set()
        elif callback_query.data in db.select_autoposting_post_name(user_id):
            await Account_use.account_use_1.set()
            channels = db.select_chats_post(user_id, callback_query.data)
            markup_inline = types.InlineKeyboardMarkup(row_width=2)
            channels_count = len(channels)
            channels_page = fnc.get_category(channels_count)
            page_here = 1
            from_page = 0
            before_page = 10
            await state.update_data(channels_count=channels_count)
            await state.update_data(channels_page=channels_page)
            await state.update_data(page_here=page_here)
            await state.update_data(from_page=from_page)
            await state.update_data(before_page=before_page)
            for channel in channels[from_page:before_page]:
                buttons = types.InlineKeyboardButton(text=channel, callback_data=channel)
                markup_inline.row(buttons)
            buttons_count = types.InlineKeyboardButton(text=f"Страница {page_here}/{channels_page} 📄", callback_data="page")
            markup_inline.add(buttons_count)
            if channels_count > 10:
                buttons_next = types.InlineKeyboardButton(text=cfg.next_page, callback_data="next_page")
                buttons_old = types.InlineKeyboardButton(text=cfg.old_page, callback_data="old_page")
                markup_inline.row(buttons_old, buttons_next)
            if db.check_date_tarife_account(user_id, callback_query.data) is None:
                pay_money_buttons = types.InlineKeyboardButton(text=cfg.pay_money_channels, callback_data='pay_money_channels')
                markup_inline.add(pay_money_buttons)
            change_keywords = types.InlineKeyboardButton(text=cfg.change_keyword_button, callback_data='change_keyword')
            back_channels = types.InlineKeyboardButton(text=cfg.back_channels, callback_data='back_channels')
            markup_inline.add(change_keywords)
            markup_inline.add(back_channels)
            await callback_query.message.edit_caption(caption=cfg.account_text_use, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
        elif callback_query.data == "add_post":
            markup_reply = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup_reply.add("Отменить")
            await callback_query.message.answer(cfg.create_account_post_1, reply_markup=markup_reply)
            await Add_post.add_post_1.set()

@dp.message_handler(state=Account_post_button.account_post_button_1)
async def accounts_button_post_1_text(message: types.Message, state: FSMContext):
    if message.chat.type == types.ChatType.PRIVATE:
        if message.text == "/cancel":
            await message.answer(cfg.cancel_sostoyanie, parse_mode=types.ParseMode.MARKDOWN)
            await state.reset_state()
        else:
            markup_inline = types.InlineKeyboardMarkup(row_width=1)
            btn1_inline = types.InlineKeyboardButton(cfg.back_button, callback_data="back_sostoyanie")
            markup_inline.add(btn1_inline)
            await message.answer(cfg.error_autoposting_texts, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)

@dp.message_handler(state=Add_post.add_post_1)
async def add_post_func_text_1(message: types.Message, state: FSMContext):
    if message.chat.type == types.ChatType.PRIVATE:
        if message.text == cfg.cancel_creategroup:
            user_id = message.from_user.id
            markup_reply = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
            markup_reply.add(cfg.autoposting)
            markup_reply.add(cfg.parser)
            markup_reply.row(cfg.my_profile, cfg.support)
            if db.select_admin(user_id) > 0:
                markup_reply.add(cfg.admin_panel_button)
            await message.answer(cfg.back_text, reply_markup=markup_reply)
            await state.reset_state()
        else:
            if message.forward_from or message.forward_from_chat:
                await state.update_data(forwarded_message_id=message.forward_from_message_id)
                await message.answer(cfg.create_account_post_2)
                await Add_post.add_post_2.set()
            else:
                await message.answer("Вы должны переслать сообщение из канала, попробуйте ещё раз:")

@dp.message_handler(state=Add_post.add_post_2)
async def add_post_func_text_2(message: types.Message, state: FSMContext):
    if message.chat.type == types.ChatType.PRIVATE:
        if message.text == cfg.cancel_creategroup:
            user_id = message.from_user.id
            markup_reply = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
            markup_reply.add(cfg.autoposting)
            markup_reply.add(cfg.parser)
            markup_reply.row(cfg.my_profile, cfg.support)
            if db.select_admin(user_id) > 0:
                markup_reply.add(cfg.admin_panel_button)
            await message.answer(cfg.back_text, reply_markup=markup_reply)
            await state.reset_state()
        else:
            if int(message.text):
                if int(message.text) >= 60:
                    current_time = datetime.datetime.now()
                    time_in_60_minutes = current_time + timedelta(minutes=60)
                    await state.update_data(time_betw=int(message.text))
                    await state.update_data(date_betw=time_in_60_minutes)
                    await message.answer(cfg.create_account_post_3)
                    await Add_post.add_post_3.set()
                else:
                    await message.answer(cfg.minimum_time_error)
            else:
                await message.answer("Ошибка! Промежуток времени должен быть цифрой, повторите ещё раз:")

@dp.message_handler(state=Add_post.add_post_3)
async def add_post_func_text_3(message: types.Message, state: FSMContext):
    if message.chat.type == types.ChatType.PRIVATE:
        user_id = message.from_user.id
        textsing = message.text
        text_line = textsing.strip().split('\n')
        text_lines = list(dict.fromkeys([element + ' ⚠' for element in text_line]))
        if message.text == cfg.cancel_creategroup:
            user_id = message.from_user.id
            markup_reply = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
            markup_reply.add(cfg.autoposting)
            markup_reply.add(cfg.parser)
            markup_reply.row(cfg.my_profile, cfg.support)
            if db.select_admin(user_id) > 0:
                markup_reply.add(cfg.admin_panel_button)
            await message.answer(cfg.back_text, reply_markup=markup_reply)
            await state.reset_state()
        else:
            if 2 <= len(message.text) <= 1000:
                if 5 <= len(text_lines) <= 50:
                    try:
                        check_number_post = db.check_numbers_account_post()
                        new_number_post = check_number_post + 1
                        data = await state.get_data()
                        number_account = data.get("number_account")
                        string_session = db.get_string_session(number_account)
                        time_betw = data.get("time_betw")
                        forwarded_message_id = data.get("forwarded_message_id")
                        db.add_post_account(user_id, forwarded_message_id, string_session, text_lines, time_betw, new_number_post)
                        markup_reply = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
                        markup_reply.add(cfg.autoposting)
                        markup_reply.add(cfg.parser)
                        markup_reply.row(cfg.my_profile, cfg.support)
                        if db.select_admin(user_id) > 0:
                            markup_reply.add(cfg.admin_panel_button)
                        await message.answer(cfg.right_create_group, reply_markup=markup_reply, parse_mode=types.ParseMode.MARKDOWN)
                        await state.finish()
                    except Exception as es:
                        await state.reset_state()
                        markup_reply = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
                        markup_reply.add(cfg.autoposting)
                        markup_reply.add(cfg.parser)
                        markup_reply.row(cfg.my_profile, cfg.support)
                        if db.select_admin(user_id) > 0:
                            markup_reply.add(cfg.admin_panel_button)
                        await message.answer(cfg.error_create_group, reply_markup=markup_reply,
                                             parse_mode=types.ParseMode.MARKDOWN)
                        print(f"[ERROR] {es}")
                else:
                    await message.answer(cfg.error_len_channels_create, parse_mode=types.ParseMode.MARKDOWN)
            else:
                await message.answer(cfg.error_len_channels, parse_mode=types.ParseMode.MARKDOWN)

@dp.callback_query_handler(state=Parsers_use.parsers_use_1)
async def parsers_use_1_button(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.message.chat.type == types.ChatType.PRIVATE:
        user_id = callback_query.from_user.id
        data = await state.get_data()
        number_group = data.get('number_group')
        channels = db.select_channels_with_number(number_group)
        check_tarife = db.check_date_tarife_for_number(number_group)
        group_name = db.select_group_name_for_number_group(user_id, number_group)
        channels_count_all = len(channels)
        channels_count = data.get("channels_count")
        channels_page = data.get("channels_page")
        page_here = data.get("page_here")
        from_page = data.get("from_page")
        before_page = data.get("before_page")
        if callback_query.data in channels:
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
                        all_channels = db.select_channels_with_number(number_group)
                        new_callback = channel_name[:-1] + '❌'
                        new_channels = [new_callback if item == channel_name else item for item in all_channels]
                        db.update_all_channels(number_group, new_channels)
                    elif channel_name[-1] == "❌":
                        all_channels = db.select_channels_with_number(number_group)
                        new_callback = channel_name[:-1] + '✅'
                        new_channels = [new_callback if item == channel_name else item for item in all_channels]
                        db.update_all_channels(number_group, new_channels)
                    elif channel_name[-1] == "⏳":
                        await callback_query.answer(cfg.error_dostup_chat, show_alert=True)
                    channels = db.select_channels_with_number(number_group)
                    markup_inline = types.InlineKeyboardMarkup(row_width=2)
                    for channel in channels[from_page:before_page]:
                        buttons = types.InlineKeyboardButton(text=channel, callback_data=channel)
                        markup_inline.row(buttons)
                    buttons_count = types.InlineKeyboardButton(text=f"Страница {page_here}/{channels_page} 📄", callback_data="page")
                    markup_inline.add(buttons_count)
                    if channels_count_all > 10:
                        buttons_next = types.InlineKeyboardButton(text=cfg.next_page, callback_data="next_page")
                        buttons_old = types.InlineKeyboardButton(text=cfg.old_page, callback_data="old_page")
                        markup_inline.row(buttons_old, buttons_next)
                    if db.check_date_tarife_for_number(number_group) is None:
                        pay_money_buttons = types.InlineKeyboardButton(text=cfg.pay_money_channels, callback_data='pay_money_channels')
                        markup_inline.add(pay_money_buttons)
                    change_keywords = types.InlineKeyboardButton(text=cfg.change_keyword_button, callback_data='change_keyword')
                    back_channels = types.InlineKeyboardButton(text=cfg.back_channels, callback_data='back_channels')
                    markup_inline.add(change_keywords)
                    markup_inline.add(back_channels)
                    await callback_query.message.edit_caption(caption=cfg.group_text_use, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
        elif callback_query.data == "next_page":
            if channels_page == page_here:
                await callback_query.answer(cfg.error_page_next, show_alert=True)
            else:
                channels = db.select_channels_with_number(number_group)
                markup_inline = types.InlineKeyboardMarkup(row_width=2)
                page_here = page_here + 1
                await state.update_data(page_here=page_here)
                await state.update_data(channels_count=channels_count)
                from_page = from_page + 10
                before_page = before_page + 10
                await state.update_data(from_page=from_page)
                await state.update_data(before_page=before_page)
                for channel in channels[from_page:before_page]:
                    buttons = types.InlineKeyboardButton(text=channel, callback_data=channel)
                    markup_inline.row(buttons)
                buttons_count = types.InlineKeyboardButton(text=f"Страница {page_here}/{channels_page} 📄", callback_data="page")
                markup_inline.add(buttons_count)
                if channels_count_all > 10:
                    buttons_next = types.InlineKeyboardButton(text=cfg.next_page, callback_data="next_page")
                    buttons_old = types.InlineKeyboardButton(text=cfg.old_page, callback_data="old_page")
                    markup_inline.row(buttons_old, buttons_next)
                if db.check_date_tarife_for_number(number_group) is None:
                    pay_money_buttons = types.InlineKeyboardButton(text=cfg.pay_money_channels, callback_data='pay_money_channels')
                    markup_inline.add(pay_money_buttons)
                change_keywords = types.InlineKeyboardButton(text=cfg.change_keyword_button, callback_data='change_keyword')
                back_channels = types.InlineKeyboardButton(text=cfg.back_channels, callback_data='back_channels')
                markup_inline.add(change_keywords)
                markup_inline.add(back_channels)
                await callback_query.message.edit_caption(caption=cfg.group_text_use, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
        elif callback_query.data == "old_page":
            print(f"{channels_count}\n{page_here}\n{from_page}\n{before_page}")
            if page_here == 1:
                await callback_query.answer(cfg.error_page_old, show_alert=True)
            else:
                channels = db.select_channels_with_number(number_group)
                markup_inline = types.InlineKeyboardMarkup(row_width=2)
                page_here = page_here - 1
                before_page = before_page - 10
                from_page = from_page - 10
                await state.update_data(from_page=from_page)
                await state.update_data(before_page=before_page)
                await state.update_data(page_here=page_here)
                await state.update_data(channels_count=channels_count)
                for channel in channels[from_page:before_page]:
                    buttons = types.InlineKeyboardButton(text=channel, callback_data=channel)
                    markup_inline.row(buttons)
                buttons_count = types.InlineKeyboardButton(text=f"Страница {page_here}/{channels_page} 📄", callback_data="page")
                markup_inline.add(buttons_count)
                if channels_count_all > 10:
                    buttons_next = types.InlineKeyboardButton(text=cfg.next_page, callback_data="next_page")
                    buttons_old = types.InlineKeyboardButton(text=cfg.old_page, callback_data="old_page")
                    markup_inline.row(buttons_old, buttons_next)
                if db.check_date_tarife_for_number(number_group) is None:
                    pay_money_buttons = types.InlineKeyboardButton(text=cfg.pay_money_channels, callback_data='pay_money_channels')
                    markup_inline.add(pay_money_buttons)
                change_keywords = types.InlineKeyboardButton(text=cfg.change_keyword_button,callback_data='change_keyword')
                back_channels = types.InlineKeyboardButton(text=cfg.back_channels, callback_data='back_channels')
                markup_inline.add(change_keywords)
                markup_inline.add(back_channels)
                await callback_query.message.edit_caption(caption=cfg.group_text_use, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
        elif callback_query.data == "back_channels":
            markup_inline = types.InlineKeyboardMarkup(row_width=1)
            group_names = db.select_group_name(user_id)
            max_buttons = 5
            for i in range(min(max_buttons, len(group_names))):
                button = types.InlineKeyboardButton(text=group_names[i], callback_data=group_names[i])
                markup_inline.add(button)

            btn_inline1 = types.InlineKeyboardButton(cfg.groups_add_button, callback_data='groups_add_button')
            btn_inline2 = types.InlineKeyboardButton(cfg.back_button, callback_data='back_groups_parser')
            markup_inline.add(btn_inline1, btn_inline2)
            await callback_query.message.edit_caption(caption=cfg.parser_text, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
            await Parser_groups_button.select_groups_button.set()
        elif callback_query.data == "pay_money_channels":
            markup_inline = types.InlineKeyboardMarkup(row_width=1)
            btn_inline1 = types.InlineKeyboardButton(cfg.confirm_oplata, callback_data='confirm_oplata')
            btn_inline2 = types.InlineKeyboardButton(cfg.back_button, callback_data='back_oplata')
            markup_inline.add(btn_inline1, btn_inline2)
            channels_len = len(channels)
            money_oplata = str(5 * int(channels_len))
            await callback_query.message.edit_caption(caption=cfg.oplata_chatov(channels_len, money_oplata), reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
        elif callback_query.data == "confirm_oplata":
            balance = db.check_balance(user_id)
            channels_len = len(channels)
            money_oplata = 5 * int(channels_len)
            if balance >= money_oplata:
                channels = db.select_channels_with_number(number_group)
                new_channels = [newer[:-2] + " ✅" for newer in channels]
                new_chan = [newer[:-2] for newer in channels]
                db.update_all_channels(number_group, new_channels)
                db.update_balance(user_id, money_oplata)
                channels_len = len(channels)
                current_data = datetime.datetime.now()
                new_date = current_data + datetime.timedelta(days=30)
                formatted_date_new = new_date.strftime("%Y-%m-%d %H:%M:%S")
                db.add_date_tariffe(user_id, formatted_date_new, number_group)
                markup_inline = types.InlineKeyboardMarkup(row_width=1)
                btn_inline1 = types.InlineKeyboardButton(cfg.menu_button, callback_data='menu_after_pay')
                markup_inline.add(btn_inline1)
                all_channels = db.select_channels_with_number(number_group)
                updated_a = [x[:-1] + '⏳' if len(x) >= 13 and x[13] == '+' else x for x in all_channels]
                db.update_all_channels(number_group, updated_a)
                await check_private_channel(new_chan, user_id, number_group)
                await state.finish()
                await callback_query.message.delete()
                await callback_query.message.answer(text=cfg.tariffe_correct(group_name, channels_len, formatted_date_new), reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
            else:
                await callback_query.answer(text=cfg.tariffe_error, show_alert=True)
        elif callback_query.data == "back_oplata":
            channels = db.select_channels_with_number(number_group)
            markup_inline = types.InlineKeyboardMarkup(row_width=2)
            for channel in channels[from_page:before_page]:
                buttons = types.InlineKeyboardButton(text=channel, callback_data=channel)
                markup_inline.row(buttons)
            buttons_count = types.InlineKeyboardButton(text=f"Страница {page_here}/{channels_page} 📄", callback_data="page")
            markup_inline.add(buttons_count)
            if channels_count_all > 10:
                buttons_next = types.InlineKeyboardButton(text=cfg.next_page, callback_data="next_page")
                buttons_old = types.InlineKeyboardButton(text=cfg.old_page, callback_data="old_page")
                markup_inline.row(buttons_old, buttons_next)
            if db.check_date_tarife_for_number(number_group) is None:
                pay_money_buttons = types.InlineKeyboardButton(text=cfg.pay_money_channels, callback_data='pay_money_channels')
                markup_inline.add(pay_money_buttons)
            change_keywords = types.InlineKeyboardButton(text=cfg.change_keyword_button, callback_data='change_keyword')
            back_channels = types.InlineKeyboardButton(text=cfg.back_channels, callback_data='back_channels')
            markup_inline.add(change_keywords)
            markup_inline.add(back_channels)
            await callback_query.message.edit_caption(caption=cfg.group_text_use, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
        elif callback_query.data == "back_sostoyanie":
            markup_inline = types.InlineKeyboardMarkup(row_width=1)
            btn_inline1 = types.InlineKeyboardButton(cfg.groups_button, callback_data='groups_parser')
            markup_inline.add(btn_inline1)
            await callback_query.message.answer_photo(photo=types.InputFile("img/testphoto.png"), caption=cfg.parser_groups_text, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
            await state.reset_state()
        elif callback_query.data == "change_keyword":
            markup_inline = types.InlineKeyboardMarkup(row_width=1)
            markup_inline.add(
                types.InlineKeyboardButton(cfg.back_button, callback_data='back_keyword')
            )
            await state.update_data(number_group=number_group)
            await callback_query.message.edit_caption(cfg.change_keyword_text, reply_markup=markup_inline)
            await Change_keyword.change_keyword_1.set()

@dp.message_handler(state=Parsers_use.parsers_use_1)
async def parsers_use_1_text(message: types.Message, state: FSMContext):
    if message.chat.type == types.ChatType.PRIVATE:
        if message.text == "/cancel":
            await message.answer(cfg.cancel_sostoyanie, parse_mode=types.ParseMode.MARKDOWN)
            await state.reset_state()
        else:
            markup_inline = types.InlineKeyboardMarkup(row_width=1)
            btn1_inline = types.InlineKeyboardButton(cfg.back_button, callback_data="back_sostoyanie")
            markup_inline.add(btn1_inline)
            await message.answer(cfg.error_parsers_texts, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)

@dp.callback_query_handler(state=Account_use.account_use_1)
async def account_use_1_button(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.message.chat.type == types.ChatType.PRIVATE:
        user_id = callback_query.from_user.id
        data = await state.get_data()
        number_group = data.get('number_group')
        channels = db.select_chats_account_with_number(number_group)
        check_tarife = db.check_date_tarife_account_for_number(number_group)
        group_name = db.select_account_name_for_number_group(user_id, number_group)
        channels_count_all = len(channels)
        channels_count = data.get("channels_count")
        channels_page = data.get("channels_page")
        page_here = data.get("page_here")
        from_page = data.get("from_page")
        before_page = data.get("before_page")
        if callback_query.data in channels:
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
                        all_channels = db.select_chats_account_with_number(number_group)
                        new_callback = channel_name[:-1] + '❌'
                        new_channels = [new_callback if item == channel_name else item for item in all_channels]
                        db.update_all_chats_account(number_group, new_channels)
                    elif channel_name[-1] == "❌":
                        all_channels = db.select_chats_account_with_number(number_group)
                        new_callback = channel_name[:-1] + '✅'
                        new_channels = [new_callback if item == channel_name else item for item in all_channels]
                        db.update_all_chats_account(number_group, new_channels)
                    elif channel_name[-1] == "⏳":
                        await callback_query.answer(cfg.error_dostup_chat, show_alert=True)
                    channels = db.select_chats_account_with_number(number_group)
                    markup_inline = types.InlineKeyboardMarkup(row_width=2)
                    for channel in channels[from_page:before_page]:
                        buttons = types.InlineKeyboardButton(text=channel, callback_data=channel)
                        markup_inline.row(buttons)
                    buttons_count = types.InlineKeyboardButton(text=f"Страница {page_here}/{channels_page} 📄", callback_data="page")
                    markup_inline.add(buttons_count)
                    if channels_count_all > 10:
                        buttons_next = types.InlineKeyboardButton(text=cfg.next_page, callback_data="next_page")
                        buttons_old = types.InlineKeyboardButton(text=cfg.old_page, callback_data="old_page")
                        markup_inline.row(buttons_old, buttons_next)
                    if db.check_date_tarife_for_number(number_group) is None:
                        pay_money_buttons = types.InlineKeyboardButton(text=cfg.pay_money_channels, callback_data='pay_money_channels')
                        markup_inline.add(pay_money_buttons)
                    change_keywords = types.InlineKeyboardButton(text=cfg.change_keyword_button, callback_data='change_keyword')
                    back_channels = types.InlineKeyboardButton(text=cfg.back_channels, callback_data='back_channels')
                    markup_inline.add(change_keywords)
                    markup_inline.add(back_channels)
                    await callback_query.message.edit_caption(caption=cfg.account_text_use, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
        elif callback_query.data == "next_page":
            if channels_page == page_here:
                await callback_query.answer(cfg.error_page_next, show_alert=True)
            else:
                channels = db.select_chats_account_with_number(number_group)
                markup_inline = types.InlineKeyboardMarkup(row_width=2)
                page_here = page_here + 1
                await state.update_data(page_here=page_here)
                await state.update_data(channels_count=channels_count)
                from_page = from_page + 10
                before_page = before_page + 10
                await state.update_data(from_page=from_page)
                await state.update_data(before_page=before_page)
                for channel in channels[from_page:before_page]:
                    buttons = types.InlineKeyboardButton(text=channel, callback_data=channel)
                    markup_inline.row(buttons)
                buttons_count = types.InlineKeyboardButton(text=f"Страница {page_here}/{channels_page} 📄", callback_data="page")
                markup_inline.add(buttons_count)
                if channels_count_all > 10:
                    buttons_next = types.InlineKeyboardButton(text=cfg.next_page, callback_data="next_page")
                    buttons_old = types.InlineKeyboardButton(text=cfg.old_page, callback_data="old_page")
                    markup_inline.row(buttons_old, buttons_next)
                if db.check_date_tarife_account_for_number(number_group) is None:
                    pay_money_buttons = types.InlineKeyboardButton(text=cfg.pay_money_channels, callback_data='pay_money_channels')
                    markup_inline.add(pay_money_buttons)
                change_keywords = types.InlineKeyboardButton(text=cfg.change_keyword_button, callback_data='change_keyword')
                back_channels = types.InlineKeyboardButton(text=cfg.back_channels, callback_data='back_channels')
                markup_inline.add(change_keywords)
                markup_inline.add(back_channels)
                await callback_query.message.edit_caption(caption=cfg.account_text_use, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
        elif callback_query.data == "old_page":
            print(f"{channels_count}\n{page_here}\n{from_page}\n{before_page}")
            if page_here == 1:
                await callback_query.answer(cfg.error_page_old, show_alert=True)
            else:
                channels = db.select_chats_account_with_number(number_group)
                markup_inline = types.InlineKeyboardMarkup(row_width=2)
                page_here = page_here - 1
                before_page = before_page - 10
                from_page = from_page - 10
                await state.update_data(from_page=from_page)
                await state.update_data(before_page=before_page)
                await state.update_data(page_here=page_here)
                await state.update_data(channels_count=channels_count)
                for channel in channels[from_page:before_page]:
                    buttons = types.InlineKeyboardButton(text=channel, callback_data=channel)
                    markup_inline.row(buttons)
                buttons_count = types.InlineKeyboardButton(text=f"Страница {page_here}/{channels_page} 📄", callback_data="page")
                markup_inline.add(buttons_count)
                if channels_count_all > 10:
                    buttons_next = types.InlineKeyboardButton(text=cfg.next_page, callback_data="next_page")
                    buttons_old = types.InlineKeyboardButton(text=cfg.old_page, callback_data="old_page")
                    markup_inline.row(buttons_old, buttons_next)
                if db.check_date_tarife_account_for_number(number_group) is None:
                    pay_money_buttons = types.InlineKeyboardButton(text=cfg.pay_money_channels, callback_data='pay_money_channels')
                    markup_inline.add(pay_money_buttons)
                change_keywords = types.InlineKeyboardButton(text=cfg.change_keyword_button,callback_data='change_keyword')
                back_channels = types.InlineKeyboardButton(text=cfg.back_channels, callback_data='back_channels')
                markup_inline.add(change_keywords)
                markup_inline.add(back_channels)
                await callback_query.message.edit_caption(caption=cfg.account_text_use, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
        elif callback_query.data == "back_channels":
            markup_inline = types.InlineKeyboardMarkup(row_width=1)
            user_id = callback_query.from_user.id
            group_names = db.select_autoposting_group_name(user_id)
            max_buttons = 5
            for i in range(min(max_buttons, len(group_names))):
                button = types.InlineKeyboardButton(text=group_names[i], callback_data=group_names[i])
                markup_inline.add(button)
            btn1_inline = types.InlineKeyboardButton(cfg.add_account_button, callback_data="add_account")
            btn2_inline = types.InlineKeyboardButton(cfg.back_button, callback_data="back_autoposting_menu")
            markup_inline.add(btn1_inline, btn2_inline)
            text = cfg.account_menu_text
            await callback_query.message.edit_caption(caption=text, reply_markup=markup_inline)
            await Accounts_button.select_accounts_button.set()
        elif callback_query.data == "pay_money_channels":
            markup_inline = types.InlineKeyboardMarkup(row_width=1)
            btn_inline1 = types.InlineKeyboardButton(cfg.confirm_oplata, callback_data='confirm_oplata')
            btn_inline2 = types.InlineKeyboardButton(cfg.back_button, callback_data='back_oplata')
            markup_inline.add(btn_inline1, btn_inline2)
            channels_len = len(channels)
            money_oplata = str(5 * int(channels_len))
            await callback_query.message.edit_caption(caption=cfg.oplata_chatov_autoposting(channels_len, money_oplata), reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
        elif callback_query.data == "confirm_oplata":
            balance = db.check_balance(user_id)
            channels_len = len(channels)
            money_oplata = 5 * int(channels_len)
            if balance >= money_oplata:
                channels = db.select_chats_account_with_number(number_group)
                new_channels = [newer[:-2] + " ✅" for newer in channels]
                db.update_all_chats_account(number_group, new_channels)
                db.update_balance(user_id, money_oplata)
                channels_len = len(channels)
                current_data = datetime.datetime.now()
                new_date = current_data + datetime.timedelta(days=30)
                formatted_date_new = new_date.strftime("%Y-%m-%d %H:%M:%S")
                db.add_date_tariffe_autoposting(user_id, formatted_date_new, number_group)
                markup_inline = types.InlineKeyboardMarkup(row_width=1)
                btn_inline1 = types.InlineKeyboardButton(cfg.menu_button, callback_data='menu_after_pay_autoposting')
                markup_inline.add(btn_inline1)
                await state.finish()
                await callback_query.message.delete()
                await callback_query.message.answer(text=cfg.tariffe_correct_autoposting(group_name, channels_len, formatted_date_new), reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
            else:
                await callback_query.answer(text=cfg.tariffe_error, show_alert=True)
        elif callback_query.data == "back_oplata":
            channels = db.select_chats_account_with_number(number_group)
            markup_inline = types.InlineKeyboardMarkup(row_width=2)
            for channel in channels[from_page:before_page]:
                buttons = types.InlineKeyboardButton(text=channel, callback_data=channel)
                markup_inline.row(buttons)
            buttons_count = types.InlineKeyboardButton(text=f"Страница {page_here}/{channels_page} 📄", callback_data="page")
            markup_inline.add(buttons_count)
            if channels_count_all > 10:
                buttons_next = types.InlineKeyboardButton(text=cfg.next_page, callback_data="next_page")
                buttons_old = types.InlineKeyboardButton(text=cfg.old_page, callback_data="old_page")
                markup_inline.row(buttons_old, buttons_next)
            if db.check_date_tarife_account_for_number(number_group) is None:
                pay_money_buttons = types.InlineKeyboardButton(text=cfg.pay_money_channels, callback_data='pay_money_channels')
                markup_inline.add(pay_money_buttons)
            change_keywords = types.InlineKeyboardButton(text=cfg.change_keyword_button, callback_data='change_keyword')
            back_channels = types.InlineKeyboardButton(text=cfg.back_channels, callback_data='back_channels')
            markup_inline.add(change_keywords)
            markup_inline.add(back_channels)
            await callback_query.message.edit_caption(caption=cfg.account_text_use, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
        elif callback_query.data == "back_sostoyanie":
            markup_inline = types.InlineKeyboardMarkup(row_width=1)
            btn_inline1 = types.InlineKeyboardButton(cfg.account_button, callback_data='accounts_button')
            markup_inline.add(btn_inline1)
            await callback_query.message.answer_photo(photo=types.InputFile("img/testphoto.png"), caption=cfg.autoposting_text, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
            await state.reset_state()

@dp.message_handler(state=Account_use.account_use_1)
async def account_use_1_texts(message: types.Message, state: FSMContext):
    if message.chat.type == types.ChatType.PRIVATE:
        if message.text == "/cancel":
            await message.answer(cfg.cancel_sostoyanie, parse_mode=types.ParseMode.MARKDOWN)
            await state.reset_state()
        else:
            markup_inline = types.InlineKeyboardMarkup(row_width=1)
            btn1_inline = types.InlineKeyboardButton(cfg.back_button, callback_data="back_sostoyanie")
            markup_inline.add(btn1_inline)
            await message.answer(cfg.error_autoposting_texts, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)

@dp.message_handler(state=Change_keyword.change_keyword_1)
async def change_keyword_1_func(message: types.Message, state: FSMContext):
    if message.chat.type == types.ChatType.PRIVATE:
        textsing = message.text
        text_lines = textsing.strip().split('\n')
        if message.text == "/cancel":
            await message.answer(cfg.cancel_sostoyanie, parse_mode=types.ParseMode.MARKDOWN)
            await state.reset_state()
        else:
            if 2 <= len(message.text) <= 500:
                if 1 <= len(text_lines) <= 20:
                    try:
                        data = await state.get_data()
                        number_group = data.get("number_group")
                        db.update_keywords(text_lines, number_group)
                        group_name = db.get_group_name_number(number_group)
                        await message.answer(cfg.correct_keyword_change(group_name), parse_mode=types.ParseMode.MARKDOWN)
                        await state.finish()
                    except Exception as es:
                        await state.reset_state()
                        await message.answer(cfg.error_change_keyword_1, parse_mode=types.ParseMode.MARKDOWN)
                        print(f"[ERROR] {es}")
                else:
                    await message.answer(cfg.error_len_keyword_create, parse_mode=types.ParseMode.MARKDOWN)
            else:
                await message.answer(cfg.error_len_keyword, parse_mode=types.ParseMode.MARKDOWN)

@dp.callback_query_handler(state=Change_keyword.change_keyword_1)
async def change_keyword_1_buttons(callback_query: types.CallbackQuery):
    if callback_query.message.chat.type == types.ChatType.PRIVATE:
        if callback_query.data == "back_keyword":
            user_id = callback_query.from_user.id
            markup_inline = types.InlineKeyboardMarkup(row_width=1)
            group_names = db.select_group_name(user_id)
            max_buttons = 5
            for i in range(min(max_buttons, len(group_names))):
                button = types.InlineKeyboardButton(text=group_names[i], callback_data=group_names[i])
                markup_inline.add(button)

            btn_inline1 = types.InlineKeyboardButton(cfg.groups_add_button, callback_data='groups_add_button')
            btn_inline2 = types.InlineKeyboardButton(cfg.back_button, callback_data='back_groups_parser')
            markup_inline.add(btn_inline1, btn_inline2)
            await Parser_groups_button.select_groups_button.set()
            await callback_query.message.edit_caption(caption=cfg.parser_text,reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
        else:
            await callback_query.answer(cfg.error_button_create_group, show_alert=True)

@dp.message_handler(state=Create_group.create_group_1)
async def create_group_func_1(message: types.Message, state: FSMContext):
    if message.chat.type == types.ChatType.PRIVATE:
        user_id = message.from_user.id
        if message.text == cfg.cancel_creategroup:
            markup_reply = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
            markup_reply.add(cfg.autoposting)
            markup_reply.add(cfg.parser)
            markup_reply.row(cfg.my_profile, cfg.support)
            if db.select_admin(user_id) > 0:
                markup_reply.add(cfg.admin_panel_button)
            await state.reset_state()
            await message.answer(cfg.cancel_creategroup_text, reply_markup=markup_reply, parse_mode=types.ParseMode.MARKDOWN)
        elif message.text:
            if 3 <= len(message.text) <= 15:
                if message.text in db.select_all_group_name():
                    await message.answer(cfg.error_name_again, parse_mode=types.ParseMode.MARKDOWN)
                else:
                    await state.update_data(group_name=message.text)
                    await message.answer(cfg.create_group_text_3, parse_mode=types.ParseMode.MARKDOWN)
                    await Create_group.create_group_2.set()
            else:
                await message.answer(cfg.error_len_name_group, parse_mode=types.ParseMode.MARKDOWN)

@dp.callback_query_handler(state=Create_group.create_group_1)
async def button_group_1(callback_query: types.CallbackQuery):
    if callback_query.data is not None:
        await callback_query.answer(cfg.error_button_create_group, show_alert=True)

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
            if db.select_admin(user_id) > 0:
                markup_reply.add(cfg.admin_panel_button)
            await state.reset_state()
            await message.answer(cfg.cancel_creategroup_text, reply_markup=markup_reply, parse_mode=types.ParseMode.MARKDOWN)
        elif message.text:
            if 2 <= len(message.text) <= 500:
                if 1 <= len(text_lines) <= 20:
                    try:
                        await state.update_data(text_lines=text_lines)
                        await message.answer(cfg.create_group_text_4, parse_mode=types.ParseMode.MARKDOWN)
                        await Create_group.create_group_3.set()
                    except Exception as es:
                        await state.reset_state()
                        markup_reply = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
                        markup_reply.add(cfg.autoposting)
                        markup_reply.add(cfg.parser)
                        markup_reply.row(cfg.my_profile, cfg.support)
                        if db.select_admin(user_id) > 0:
                            markup_reply.add(cfg.admin_panel_button)
                        await message.answer(cfg.error_create_group, reply_markup=markup_reply, parse_mode=types.ParseMode.MARKDOWN)
                        print(f"[ERROR] {es}")
                else:
                    await message.answer(cfg.error_len_keyword_create, parse_mode=types.ParseMode.MARKDOWN)
            else:
                await message.answer(cfg.error_len_keyword, parse_mode=types.ParseMode.MARKDOWN)

@dp.callback_query_handler(state=Create_group.create_group_2)
async def button_group_2(callback_query: types.CallbackQuery):
    if callback_query.data is not None:
        await callback_query.answer(cfg.error_button_create_group, show_alert=True)

@dp.message_handler(state=Create_group.create_group_3)
async def create_group_func_3(message: types.Message, state: FSMContext):
    if message.chat.type == types.ChatType.PRIVATE:
        user_id = message.from_user.id
        textsing = message.text
        text_line = textsing.strip().split('\n')
        text_lines = list(dict.fromkeys([element + ' ⚠' for element in text_line]))
        if message.text == cfg.cancel_creategroup:
            markup_reply = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
            markup_reply.add(cfg.autoposting)
            markup_reply.add(cfg.parser)
            markup_reply.row(cfg.my_profile, cfg.support)
            if db.select_admin(user_id) > 0:
                markup_reply.add(cfg.admin_panel_button)
            await state.reset_state()
            await message.answer(cfg.cancel_creategroup_text, reply_markup=markup_reply, parse_mode=types.ParseMode.MARKDOWN)
        elif message.text:
            if 2 <= len(message.text) <= 1000:
                if 5 <= len(text_lines) <= 50:
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
                        if db.select_admin(user_id) > 0:
                            markup_reply.add(cfg.admin_panel_button)
                        await message.answer(cfg.right_create_group, reply_markup=markup_reply, parse_mode=types.ParseMode.MARKDOWN)
                        await state.finish()
                    except Exception as es:
                        await state.reset_state()
                        markup_reply = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
                        markup_reply.add(cfg.autoposting)
                        markup_reply.add(cfg.parser)
                        markup_reply.row(cfg.my_profile, cfg.support)
                        if db.select_admin(user_id) > 0:
                            markup_reply.add(cfg.admin_panel_button)
                        await message.answer(cfg.error_create_group, reply_markup=markup_reply, parse_mode=types.ParseMode.MARKDOWN)
                        print(f"[ERROR] {es}")
                else:
                    await message.answer(cfg.error_len_channels_create, parse_mode=types.ParseMode.MARKDOWN)
            else:
                await message.answer(cfg.error_len_channels, parse_mode=types.ParseMode.MARKDOWN)

@dp.callback_query_handler(state=Create_group.create_group_3)
async def button_group_2(callback_query: types.CallbackQuery):
    if callback_query.data is not None:
        await callback_query.answer(cfg.error_button_create_group, show_alert=True)

@dp.message_handler(state=Add_chat_ids.panel_adm)
async def panel_adm(message: types.Message, state: FSMContext):
    if message.text == cfg.cancel_creategroup:
        markup_reply = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
        markup_reply.add(cfg.autoposting)
        markup_reply.add(cfg.parser)
        markup_reply.row(cfg.my_profile, cfg.support)
        markup_reply.add(cfg.admin_panel_button)
        await message.answer(cfg.panel_admin_back_text, reply_markup=markup_reply, parse_mode=types.ParseMode.MARKDOWN)
        await state.reset_state()
    elif message.text == cfg.add_chat_id_button:
        markup_reply = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        markup_reply.add(cfg.back_button)
        await message.answer(cfg.write_number_group_text, reply_markup=markup_reply, parse_mode=types.ParseMode.MARKDOWN)
        await Add_chat_ids.add_ids_1.set()
    else:
        await message.answer(cfg.error_text_in_state_panel, parse_mode=types.ParseMode.MARKDOWN)

@dp.message_handler(state=Add_chat_ids.add_ids_1)
async def add_chat_ids_num_1(message: types.Message, state: FSMContext):
    if message.text == cfg.cancel_creategroup:
        markup_reply = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        markup_reply.add(cfg.add_chat_id_button, cfg.back_button)
        await message.answer(cfg.cancel_add_ids, reply_markup=markup_reply, parse_mode=types.ParseMode.MARKDOWN)
        await Add_chat_ids.panel_adm.set()
    else:
        try:
            message_text = int(message.text)
            await state.update_data(number_group=message_text)
            await message.answer(cfg.write_chat_ids_text, parse_mode=types.ParseMode.MARKDOWN)
            await Add_chat_ids.add_ids_2.set()
        except Exception as err:
            await message.answer(cfg.error_write_number_group_text, parse_mode=types.ParseMode.MARKDOWN)
            await Add_chat_ids.add_ids_1.set()

@dp.message_handler(state=Add_chat_ids.add_ids_2)
async def add_chat_ids_num_2(message: types.Message, state: FSMContext):
    if message.text == cfg.cancel_creategroup:
        markup_reply = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        markup_reply.add(cfg.add_chat_id_button, cfg.back_button)
        await message.answer(cfg.cancel_add_ids, reply_markup=markup_reply, parse_mode=types.ParseMode.MARKDOWN)
        await Add_chat_ids.panel_adm.set()
    else:
        markup_reply = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        markup_reply.add(cfg.add_chat_id_button, cfg.back_button)
        textsing = message.text
        text_lines = textsing.strip().split('\n')
        new_lst = []
        data = await state.get_data()
        number_group = data.get("number_group")
        for lines in text_lines:
            try:
                int(lines[3:])
                new_lst.append(lines)
                all_channels = db.select_channels_with_number(number_group)
                channels_link = [item for item in all_channels if len(item) >= 13 and item[13] == '+']
                index = int(lines.split(')')[0]) - 1
                channels_link[index] = channels_link[index].replace("⏳", "✅")
                owner_lst = [next((full_word for full_word in channels_link if full_word[:-2] == word[:-2]), word) for word in all_channels]
                db.update_all_channels(number_group, owner_lst)
            except Exception:
                await message.answer(cfg.error_add_ids, reply_markup=markup_reply, parse_mode=types.ParseMode.MARKDOWN)
                await Add_chat_ids.panel_adm.set()
        old_chat_list = db.select_chat_ids(number_group) or []
        new_lst = old_chat_list + new_lst
        db.add_chat_ids(int(number_group), new_lst)
        await message.answer(cfg.correct_add_chat_ids, reply_markup=markup_reply, parse_mode=types.ParseMode.MARKDOWN)
        await Add_chat_ids.panel_adm.set()

@dp.message_handler(state=Create_account_autoposting.create_autoposting_1)
async def process_phone(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    markup_reply = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
    markup_reply.add(cfg.autoposting)
    markup_reply.add(cfg.parser)
    markup_reply.row(cfg.my_profile, cfg.support)
    await client.connect()
    if db.select_admin(user_id) > 0:
        markup_reply.add(cfg.admin_panel_button)
    if message.text == cfg.cancel_creategroup:
        await message.answer(cfg.back_text, reply_markup=markup_reply)
        await state.reset_state()
    else:
        if db.get_states_sms(user_id) == 1:
            phone = message.text
            if not client.is_connected():
                await client.connect()

            try:
                result = await client.send_code_request(phone)
                phone_code_hash = result.phone_code_hash
                await state.update_data(phone=phone)
                await state.update_data(phone_code_hash=phone_code_hash)
                db.update_states_sms(user_id, 2)
                await message.reply("Теперь отправьте код, который вы получили от Telegram.\n\nВажно! Пожалуйста, НЕ присылай мне код как есть (иначе он сразу перестанет действовать). Пришли мне его, разделив цифры пробелами или любыми другими символами. Например, 123 45 или 1 2345 или 123a45, где 12345 - это сам код, который ты получил от Телеграма.")
            except Exception as e:
                logging.error(f"Ошибка при отправке кода: {e}")
                await message.reply("Произошла ошибка при отправке кода, пожалуйста, попробуйте еще раз ввести номер телефона:")
        elif db.get_states_sms(user_id) == 2:
            code_spaces = message.text
            code = code_spaces.replace(" ", "")
            data = await state.get_data()
            phone = data.get("phone")
            phone_code_hash = data.get("phone_code_hash")
            try:
                await client.sign_in(phone, int(code), phone_code_hash=phone_code_hash)
                string_session = client.session.save()
                await state.update_data(string_session=string_session)
                await Create_account_autoposting.create_autoposting_2.set()
                await message.reply(cfg.create_account_autoposting_3)
            except SessionPasswordNeededError:
                db.update_states_sms(user_id, 3)
                await message.reply("Требуется пароль для двухфакторной аутентификации. Введите его здесь:")
            except PhoneCodeExpiredError:
                await message.reply("Код подтверждения истек. Попробуйте начать заново.", reply_markup=markup_reply)
                await state.finish()
            except PhoneNumberUnoccupiedError:
                await message.reply("Этот номер телефона не зарегистрирован в Telegram.", reply_markup=markup_reply)
                await state.finish()
            except Exception as e:
                await message.reply(f"Произошла ошибка: {str(e)}", reply_markup=markup_reply)
                await state.finish()
        elif db.get_states_sms(user_id) == 3:
            password = message.text
            try:
                await client.sign_in(password=password)
                string_session = client.session.save()
                await Create_account_autoposting.create_autoposting_2.set()
                await state.update_data(string_session=string_session)
                await message.answer(cfg.create_account_autoposting_3)
            except Exception as e:
                await message.reply(str(e), reply_markup=markup_reply)
                await state.finish()

@dp.message_handler(state=Create_account_autoposting.create_autoposting_2)
async def group_name_autoposting(message: types.Message, state: FSMContext):
    if message.chat.type == types.ChatType.PRIVATE:
        user_id = message.from_user.id
        if message.text == cfg.cancel_creategroup:
            markup_reply = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
            markup_reply.add(cfg.autoposting)
            markup_reply.add(cfg.parser)
            markup_reply.row(cfg.my_profile, cfg.support)
            if db.select_admin(user_id) > 0:
                markup_reply.add(cfg.admin_panel_button)
            await message.answer(cfg.back_text, reply_markup=markup_reply)
            await state.reset_state()
        else:
            if 3 <= len(message.text) <= 15:
                data = await state.get_data()
                phone = data.get('phone')
                string_session = data.get('string_session')
                group_name = message.text
                check_number_group = db.check_numbers_account_autoposting()
                new_number_group = check_number_group + 1
                db.add_autoposting_account(user_id, new_number_group, phone, string_session, group_name)
                await message.answer(cfg.create_account_autoposting_4)
                await state.finish()
            else:
                await message.answer("Минимальная длина названия аккаунта, должна быть 3, максимальная 15, попробуйте ещё раз:")


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
        elif message.text == cfg.admin_panel_button:
            await panel_administration(message)


async def on_startup(_):
    asyncio.create_task(search_and_forward())
    asyncio.create_task(search_and_forward_close_group())
    # asyncio.create_task(autoposting_forward())

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)