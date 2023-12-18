from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.storage import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from datbas import Data
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError, ChannelPrivateError, ChatForbiddenError, UserPrivacyRestrictedError, PeerIdInvalidError, SessionPasswordNeededError, PhoneCodeExpiredError, PhoneNumberUnoccupiedError, RPCError
from bs4 import BeautifulSoup
import requests
import functions as fnc
import asyncio
import config as cfg
import logging
import datetime
import json
import re
import pytz

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

def validate_time_format(time_str):
    # Регулярное выражение для проверки формата времени
    pattern = r'^\d{2}:\d{2}$'

    # Проверка соответствия строки шаблону
    if re.match(pattern, time_str):
        return True
    else:
        return False

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
        for adm_id in cfg.admin_id:
            await bot.send_message(adm_id, f"{fnc.nick_with_link('Пользователь', user_id)}, добавил закрытые чаты, вам необходимо подписаться на них.\n\n{channels_link}\n\nНомер группы - {str(number_group)}", parse_mode=types.ParseMode.MARKDOWN)

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

    while True:
        try:
            groups = db.select_all_channels_group()
            if not groups:
                await asyncio.sleep(10)
                continue

            group = groups[num]
            user_id, chat_idn, keywords, data_end, group_name, chat_name = group[0], group[2], group[5], group[3], group[4], group[8]
            chat_ids = [item for item in chat_idn if item.endswith('✅')]
            chat_ids = [item for item in chat_ids if len(item) < 13 or item[13] != '+']

            number_group = group[1]

            current_date = datetime.datetime.now()
            formated_base = datetime.datetime.strptime(data_end, "%Y-%m-%d %H:%M:%S")
            if formated_base > current_date:
                for chat_id_name in chat_name:
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
                            all_channels_name = db.select_channels_name_with_number(number_group)
                            new_callback_name = chat_id_name[:-1] + '⏳'
                            new_channels_name = [new_callback_name if item == chat_id_name else item for item in all_channels_name]
                            db.update_all_channels_name(number_group, new_channels_name)
                            await asyncio.sleep(2)
                            exception_occurred = True
                        finally:
                            if exception_occurred is False:
                                messages = await telethon_client.get_messages(trimmed_chat_id, limit=1)
                                if messages:
                                    last_message_ids[trimmed_chat_id] = messages[0].id
                                else:
                                    pass
            else:
                db.delete_data_end_group(number_group)
                formated_chat_idn = [s.replace('✅', '⚠') for s in chat_idn]
                db.update_all_channels(number_group, formated_chat_idn)
                await bot.send_message(user_id, cfg.end_data_group_text(group_name))

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

    while True:
        try:
            groups = db.select_all_channels_group()
            if not groups:
                await asyncio.sleep(10)
                continue

            group = groups[num]
            user_id, chat_ids, keywords, channelss_link, data_end, group_name, channels_name = group[0], group[8], group[5], group[2], group[3], group[4], group[7]
            channels_link = [item for item in channelss_link if len(item) >= 13 and item[13] == '+']
            number_group = group[1]
            current_date = datetime.datetime.now()
            formated_base = datetime.datetime.strptime(data_end, "%Y-%m-%d %H:%M:%S")
            if formated_base > current_date:
                if chat_ids is not None:
                    for chat_id_name in channels_name:
                        for chat_id in chat_ids:
                            index_chat_id = int(chat_id[0][0])
                            links_1 = channels_link[index_chat_id - 1]
                            links_2 = links_1[-1]
                            if links_2 == "✅":
                                trimmed_chat_ids = int(chat_id[0][3:])
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
            else:
                db.delete_data_end_group(number_group)
                formated_chat_idn = [s.replace('✅', '⚠') for s in channelss_link]
                formated_chat_id_name = [s.replace('✅', '⚠') for s in channels_name]
                db.update_all_channels(number_group, formated_chat_idn)
                db.update_all_channels_name(number_group, formated_chat_id_name)
                await bot.send_message(user_id, cfg.end_data_group_text(group_name))
            num += 1
            if num >= len(groups):
                num = 0

        except Exception as e:
            print(f"Произошла ошибка: {type(e).__name__}")
            await asyncio.sleep(2)

        await asyncio.sleep(1)

async def autoposting_forward():
    num = 0

    groups_count = len(db.select_all_channels_autoposting_post_not_null())
    while True:
        try:
            groups = db.select_all_channels_autoposting_post_not_null()
            if not groups:
                await asyncio.sleep(10)
                continue
            moscow_tz = pytz.timezone('Europe/Moscow')
            group = groups[num]
            user_id, chat_ids, string_session, message_id, number_group, data_end, channel_tag = group[0], group[10], group[2], group[1], group[4], group[3], group[6]
            # chat_ids = [sublist for sublist in chat_idn if '✅' in sublist[0]]
            current_date = datetime.datetime.now(moscow_tz)
            formated_base = datetime.datetime.strptime(data_end, "%Y-%m-%d %H:%M:%S")
            formated_base = moscow_tz.localize(formated_base)
            if formated_base > current_date:
                if chat_ids != []:
                    current_date = datetime.datetime.now(moscow_tz)
                    for chat_id in chat_ids:
                        formated_chat_id = chat_id[0][:-2]
                        date_betw = chat_id[1:]
                        for date_bet in date_betw:
                            if chat_id[0][-1] == "✅":
                                formated_base = datetime.datetime.strptime(date_bet, "%Y-%m-%d %H:%M:%S")
                                formated_base = moscow_tz.localize(formated_base)
                                if current_date > formated_base:
                                    async with TelegramClient(StringSession(string_session), cfg.API_ID, cfg.API_HASH) as telethon_client_autoposting:
                                            try:
                                                await telethon_client_autoposting.forward_messages(entity=formated_chat_id, messages=int(message_id), from_peer=channel_tag)
                                                await bot.send_message(user_id, f"Рекламный пост, успешно отправлен в чат {formated_chat_id}")
                                                await asyncio.sleep(5)
                                            except RPCError as err:
                                                print(f"[ERROR RPCError] {err}")
                                            except Exception as erri:
                                                print(f"[ERROR EXCEPTION] {erri}")
                                    time_in_60_minutes = formated_base + datetime.timedelta(minutes=1440)
                                    formatted_date_new = time_in_60_minutes.strftime("%Y-%m-%d %H:%M:%S")
                                    new_channels = [formatted_date_new if item == date_bet else item for item in chat_id]
                                    chat_idln = db.select_chats_account_with_number_autoposting(number_group)
                                    new_updates = [new_channels if item == chat_id else item for item in chat_idln]
                                    json_data = json.dumps(new_updates)
                                    db.update_chat_idn_autoposting(json_data, number_group)
            else:
                db.delete_data_end_post(number_group)
                formated_chat_idn = [s.replace('✅', '⚠') for s in chat_ids]
                db.update_chats_post(formated_chat_idn, number_group)
                await bot.send_message(user_id, cfg.end_data_post_text(message_id))

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

class Change_keyword(StatesGroup):
    change_keyword_1 = State()

class Add_chat_ids(StatesGroup):
    panel_adm = State()
    add_ids_1 = State()
    add_ids_2 = State()


class Add_post(StatesGroup):
    add_post_1 = State()
    add_post_2 = State()
    add_post_3 = State()
    add_post_4 = State()

class Change_time_betw(StatesGroup):
    change_time_betw_1 = State()

class Add_time_autoposting_chat(StatesGroup):
    add_time_autoposting_1 = State()

class Change_time_autoposting_chat(StatesGroup):
    change_time_autoposting_1 = State()

async def profile(message):
    user_id = message.from_user.id
    markup_inline = types.InlineKeyboardMarkup(row_width=1, )
    btn_inline1 = types.InlineKeyboardButton(cfg.up_balance, callback_data='up_balance')
    markup_inline.add(btn_inline1)
    await message.answer_photo(photo=types.InputFile("img/photo1.jpg"), caption=cfg.profile(user_id, db.select_balance(user_id)), reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)

async def supports_send(message):
    markup_inline = types.InlineKeyboardMarkup(row_width=1)
    btn_inline1 = types.InlineKeyboardButton(cfg.support, callback_data='support', url=f"tg://user?id={cfg.admin_id[1]}")
    markup_inline.add(btn_inline1)
    await message.answer(cfg.support_text, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)

async def parsers_send(message):
    user_id = message.from_user.id
    markup_inline = types.InlineKeyboardMarkup(row_width=1)
    group_names = db.select_group_name(user_id)
    max_buttons = 5
    for i in range(min(max_buttons, len(group_names))):
        button = types.InlineKeyboardButton(text=group_names[i], callback_data=group_names[i])
        markup_inline.add(button)

    btn_inline1 = types.InlineKeyboardButton(cfg.groups_add_button, callback_data='groups_add_button_parser')
    markup_inline.add(btn_inline1)
    await message.answer_photo(photo=types.InputFile("img/testphoto.png"), caption=cfg.parser_text, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)

async def autoposting_send(message):
    markup_inline = types.InlineKeyboardMarkup(row_width=1)
    user_id = message.from_user.id
    group_names = db.select_autoposting_group_name(user_id)
    max_buttons = 5
    for i in range(min(max_buttons, len(group_names))):
        button = types.InlineKeyboardButton(text=group_names[i], callback_data=group_names[i])
        markup_inline.add(button)
    btn1_inline = types.InlineKeyboardButton(cfg.add_account_button, callback_data="add_account_autoposting")
    markup_inline.add(btn1_inline)
    if group_names is None:
        text = cfg.accounts_left_text
    else:
        text = cfg.accounts_right_text
    await message.answer_photo(photo=types.InputFile("img/testphoto.png"), caption=text, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)

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

        await message.answer(cfg.start_text(first_name), reply_markup=markup_reply, parse_mode=types.ParseMode.MARKDOWN)
        await profile(message)

@dp.message_handler(commands=['send_message'])
async def send_message(message: types.Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) == 3:
        command, user_id, message = parts
    else:
        command = user_id = message = None
    await bot.send_message(user_id, message)
    print("успешно отправлено")

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
        if callback_query.data == "menu_after_pay_parser":
            try:
                user_id = callback_query.from_user.id
                markup_inline = types.InlineKeyboardMarkup(row_width=1)
                group_names = db.select_group_name(user_id)
                max_buttons = 5
                for i in range(min(max_buttons, len(group_names))):
                    button = types.InlineKeyboardButton(text=group_names[i], callback_data=group_names[i])
                    markup_inline.add(button)
                btn_inline1 = types.InlineKeyboardButton(cfg.groups_add_button, callback_data='groups_add_button_parser')
                markup_inline.add(btn_inline1)
                await callback_query.message.answer_photo(photo=types.InputFile("img/testphoto.png"), caption=cfg.parser_text, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
            except Exception:
                await callback_query.answer("Произошла ошибка при нажатии на кнопку Меню для Парсера", show_alert=True)
        elif callback_query.data == "menu_after_pay_autoposting":
            try:
                markup_inline = types.InlineKeyboardMarkup(row_width=1)
                user_id = callback_query.from_user.id
                group_names = db.select_autoposting_group_name(user_id)
                max_buttons = 5
                for i in range(min(max_buttons, len(group_names))):
                    button = types.InlineKeyboardButton(text=group_names[i], callback_data=group_names[i])
                    markup_inline.add(button)
                btn1_inline = types.InlineKeyboardButton(cfg.add_account_button, callback_data="add_account_autoposting")
                markup_inline.add(btn1_inline)
                if group_names is None:
                    text = cfg.accounts_left_text
                else:
                    text = cfg.accounts_right_text
                await callback_query.message.answer_photo(photo=types.InputFile("img/testphoto.png"), caption=text, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
            except Exception:
                await callback_query.answer("Произошла ошибка при нажатии на кнопку Меню для Автопостинга", show_alert=True)
        elif callback_query.data == "groups_add_button_parser":
            try:
                number_group_parser = db.check_number_group(user_id)
                if int(number_group_parser) < 5:
                    markup_reply = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
                    markup_reply.add(cfg.cancel_creategroup)
                    await Create_group.create_group_1.set()
                    await callback_query.message.answer(cfg.create_group_text_1, parse_mode=types.ParseMode.MARKDOWN)
                    await callback_query.message.answer(cfg.create_group_text_2, reply_markup=markup_reply, parse_mode=types.ParseMode.MARKDOWN)
                else:
                    await callback_query.answer(cfg.error_group_5, show_alert=True)
            except Exception:
                await callback_query.answer("Произошла ошибка при нажатии на кнопку добавления группы, нажмите ещё раз на нижнюю кнопку 'Парсер' и повторите попытку.", show_alert=True)
        elif callback_query.data in db.select_group_name(user_id):
            try:
                number_group_parser = db.select_number_group(user_id, callback_query.data)
                await state.update_data(number_group_parser=number_group_parser)
                channels_parser = db.select_channels(user_id, callback_query.data)
                channels_name_parser = db.select_channels_name(user_id, callback_query.data)
                markup_inline = types.InlineKeyboardMarkup(row_width=2)
                channels_count_parser= len(channels_parser)
                channels_page_parser = fnc.get_category(channels_count_parser)
                page_here_parser = 1
                from_page_parser = 0
                before_page_parser = 10
                await state.update_data(channels_count_parser=channels_count_parser)
                await state.update_data(channels_page_parser=channels_page_parser)
                await state.update_data(page_here_parser=page_here_parser)
                await state.update_data(from_page_parser=from_page_parser)
                await state.update_data(before_page_parser=before_page_parser)
                paired_channels = zip(channels_name_parser[from_page_parser:before_page_parser], channels_parser[from_page_parser:before_page_parser])
                for channel_name, channel in paired_channels:
                    button = types.InlineKeyboardButton(text=channel_name, callback_data=channel)
                    markup_inline.row(button)
                buttons_count = types.InlineKeyboardButton(text=f"Страница {page_here_parser}/{channels_page_parser} 📄", callback_data="page_parser")
                markup_inline.add(buttons_count)
                if channels_count_parser > 10:
                    buttons_next = types.InlineKeyboardButton(text=cfg.next_page, callback_data="next_page_parser")
                    buttons_old = types.InlineKeyboardButton(text=cfg.old_page, callback_data="old_page_parser")
                    markup_inline.row(buttons_old, buttons_next)
                if db.check_date_tarife(user_id, callback_query.data) is None:
                    pay_money_buttons = types.InlineKeyboardButton(text=cfg.pay_money_channels, callback_data='pay_money_channels_parser')
                    markup_inline.add(pay_money_buttons)
                change_keywords = types.InlineKeyboardButton(text=cfg.change_keyword_button, callback_data='change_keyword_parser')
                back_channels = types.InlineKeyboardButton(text=cfg.back_channels, callback_data='back_channels_parser')
                markup_inline.add(change_keywords)
                markup_inline.add(back_channels)
                await callback_query.message.edit_caption(caption=cfg.group_text_use, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
            except Exception:
                await callback_query.answer("Произошла ошибка при нажатии на группу, возможно группы не существует, пожалуйста нажмите на нижнюю кнопку 'Парсер' и повторите попытку.", show_alert=True)
        elif callback_query.data == "back_sostoyanie_parser":
            try:
                user_id = callback_query.from_user.id
                markup_inline = types.InlineKeyboardMarkup(row_width=1)
                group_names = db.select_group_name(user_id)
                max_buttons = 5
                for i in range(min(max_buttons, len(group_names))):
                    button = types.InlineKeyboardButton(text=group_names[i], callback_data=group_names[i])
                    markup_inline.add(button)
                btn_inline1 = types.InlineKeyboardButton(cfg.groups_add_button, callback_data='groups_add_button_parser')
                markup_inline.add(btn_inline1)
                await callback_query.message.answer_photo(photo=types.InputFile("img/testphoto.png"), caption=cfg.parser_text, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
            except Exception:
                await callback_query.answer("Произошла ошибка при нажатии на кнопку выхода из состоянии, пожалуйста нажмите на нижнюю кнопку 'Парсер' и повторите попытку.", show_alert=True)
        elif callback_query.data == "add_account_autoposting":
            try:
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
            except Exception:
                await callback_query.answer("Произошла ошибка при нажатии на кнопку выхода из состоянии, пожалуйста нажмите на нижнюю кнопку 'Парсер' и повторите попытку.", show_alert=True)
        elif callback_query.data in db.select_account_name(user_id):
            try:
                number_account = db.select_account_number(user_id, callback_query.data)
                await state.update_data(number_account=number_account)
                markup_inline = types.InlineKeyboardMarkup(row_width=1)
                user_id = callback_query.from_user.id
                group_names = db.select_autoposting_post_name_for_number(user_id, number_account)
                max_buttons = 5
                for i in range(min(max_buttons, len(group_names))):
                    button = types.InlineKeyboardButton(text=group_names[i], callback_data=group_names[i])
                    markup_inline.add(button)
                btn1_inline = types.InlineKeyboardButton(cfg.add_post_button, callback_data="add_post_autoposting")
                btn2_inline = types.InlineKeyboardButton(cfg.back_button, callback_data="back_autoposting_account")
                markup_inline.add(btn1_inline, btn2_inline)
                await callback_query.message.edit_caption(caption=cfg.posts_right_text, reply_markup=markup_inline)
            except Exception:
                await callback_query.answer("Произошла ошибка при нажатии на аккаунта для автопостинга, пожалуйста нажмите на нижнюю кнопку 'Автопостинг' и повторите попытку.", show_alert=True)
        elif callback_query.data == "back_sostoyanie_autoposting":
            try:
                markup_inline = types.InlineKeyboardMarkup(row_width=1)
                user_id = callback_query.from_user.id
                group_names = db.select_autoposting_group_name(user_id)
                max_buttons = 5
                for i in range(min(max_buttons, len(group_names))):
                    button = types.InlineKeyboardButton(text=group_names[i], callback_data=group_names[i])
                    markup_inline.add(button)
                btn1_inline = types.InlineKeyboardButton(cfg.add_account_button, callback_data="add_account_autoposting")
                markup_inline.add(btn1_inline)
                if group_names is None:
                    text = cfg.accounts_left_text
                else:
                    text = cfg.accounts_right_text
                await callback_query.message.answer_photo(photo=types.InputFile("img/testphoto.png"), caption=text, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
            except Exception:
                await callback_query.answer("Произошла ошибка при нажатии на кнопку выхода из состояния аккаунта для автопостинга, пожалуйста нажмите на нижнюю кнопку 'Автопостинг' и повторите попытку.", show_alert=True)
        elif callback_query.data == "back_autoposting_account":
            try:
                markup_inline = types.InlineKeyboardMarkup(row_width=1)
                user_id = callback_query.from_user.id
                group_names = db.select_autoposting_group_name(user_id)
                max_buttons = 5
                for i in range(min(max_buttons, len(group_names))):
                    button = types.InlineKeyboardButton(text=group_names[i], callback_data=group_names[i])
                    markup_inline.add(button)
                btn1_inline = types.InlineKeyboardButton(cfg.add_account_button, callback_data="add_account_autoposting")
                markup_inline.add(btn1_inline)
                if group_names is None:
                    text = cfg.accounts_left_text
                else:
                    text = cfg.accounts_right_text
                await callback_query.message.edit_caption(caption=text, reply_markup=markup_inline)
            except Exception:
                await callback_query.answer("Произошла ошибка при нажатии на кнопку выхода из аккаунта для автопостинга, пожалуйста нажмите на нижнюю кнопку 'Автопостинг' и повторите попытку.", show_alert=True)
        elif callback_query.data in db.select_autoposting_post_name(user_id):
            try:
                channels = db.select_chats_post(user_id, callback_query.data)
                channels_name = db.select_chats_name_post(user_id, callback_query.data)
                markup_inline = types.InlineKeyboardMarkup(row_width=1)
                channels_count_autoposting = len(channels)
                channels_page_autoposting = fnc.get_category(channels_count_autoposting)
                number_post_autoposting = db.select_number_post(user_id, callback_query.data)
                await state.update_data(number_post_autoposting=number_post_autoposting)
                await state.update_data(post_name_autoposting=callback_query.data)
                page_here_autoposting = 1
                from_page_autoposting = 0
                before_page_autoposting = 10
                await state.update_data(channels_count_autoposting=channels_count_autoposting)
                await state.update_data(channels_page_autoposting=channels_page_autoposting)
                await state.update_data(page_here_autoposting=page_here_autoposting)
                await state.update_data(from_page_autoposting=from_page_autoposting)
                await state.update_data(before_page_autoposting=before_page_autoposting)
                paired_channels = zip(channels_name[from_page_autoposting:before_page_autoposting], channels[from_page_autoposting:before_page_autoposting])
                for channel_name, channel in paired_channels:
                    buttons = types.InlineKeyboardButton(text=channel_name, callback_data=channel)
                    markup_inline.row(buttons)
                buttons_count = types.InlineKeyboardButton(text=f"Страница {page_here_autoposting}/{channels_page_autoposting} 📄", callback_data="page_autoposting")
                markup_inline.add(buttons_count)
                if channels_count_autoposting > 10:
                    buttons_next = types.InlineKeyboardButton(text=cfg.next_page, callback_data="next_page_autoposting")
                    buttons_old = types.InlineKeyboardButton(text=cfg.old_page, callback_data="old_page_autoposting")
                    markup_inline.row(buttons_old, buttons_next)
                if db.check_date_tarife_account(user_id, callback_query.data) is None:
                    pay_money_buttons = types.InlineKeyboardButton(text=cfg.pay_money_channels, callback_data='pay_money_channels_autoposting')
                    markup_inline.add(pay_money_buttons)
                back_channels = types.InlineKeyboardButton(text=cfg.back_channels, callback_data='back_channels_autoposting')
                delete_post_button = types.InlineKeyboardButton(text=cfg.delete_post_button, callback_data="delete_post_autoposting")
                markup_inline.add(delete_post_button, back_channels)
                message_id_bot = db.select_post_name(callback_query.data)
                await bot.forward_message(chat_id=user_id, from_chat_id=user_id, message_id=message_id_bot)
                await callback_query.message.edit_caption(caption=cfg.account_text_use, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
            except Exception:
                await callback_query.answer("Произошла ошибка при нажатии на аккаунта для автопостинга, пожалуйста нажмите на нижнюю кнопку 'Автопостинг' и повторите попытку.", show_alert=True)
        elif callback_query.data == "add_post_autoposting":
            try:
                markup_reply = types.ReplyKeyboardMarkup(resize_keyboard=True)
                markup_reply.add("Отменить")
                await callback_query.message.answer(cfg.create_account_post_1, reply_markup=markup_reply)
                await Add_post.add_post_1.set()
            except Exception:
                await callback_query.answer("Произошла ошибка при нажатии на кнопку добавления аккаунта для автопостинга, пожалуйста нажмите на нижнюю кнопку 'Автопостинг' и повторите попытку.", show_alert=True)
        data = await state.get_data()
        number_group_parser = data.get('number_group_parser')
        if number_group_parser is not None:
            channels_parser = db.select_channels_with_number(number_group_parser)
            check_tarife_parser = db.check_date_tarife_for_number(number_group_parser)
            group_name_parser = db.select_group_name_for_number_group(user_id, number_group_parser)
            channels_count_all_parser = len(channels_parser)
            channels_count_parser = data.get("channels_count_parser")
            channels_page_parser = data.get("channels_page_parser")
            page_here_parser = data.get("page_here_parser")
            from_page_parser = data.get("from_page_parser")
            before_page_parser = data.get("before_page_parser")
            if callback_query.data in channels_parser:
                if check_tarife_parser is None:
                    await callback_query.answer(text=cfg.error_oplata, show_alert=True)
                else:
                    current_data = datetime.datetime.now()
                    formated_check_date_tarife = datetime.datetime.strptime(check_tarife_parser, "%Y-%m-%d %H:%M:%S")
                    if current_data >= formated_check_date_tarife:
                        db.delete_old_tariffe(user_id, number_group_parser)
                        await callback_query.answer(text=cfg.error_oplata, show_alert=True)
                    else:
                        channel_name = callback_query.data
                        if channel_name[-1] == "✅":
                            group_index = channels_parser.index(channel_name)
                            all_channels_name_parser = db.select_channels_name_with_number(number_group_parser)
                            group_name = all_channels_name_parser[group_index]
                            all_channels = db.select_channels_with_number(number_group_parser)
                            new_callback = channel_name[:-1] + '❌'
                            new_channels = [new_callback if item == channel_name else item for item in all_channels]
                            db.update_all_channels(number_group_parser, new_channels)
                            new_callback_name = group_name[:-1] + '❌'
                            new_channels_name = [new_callback_name if item == group_name else item for item in all_channels_name_parser]
                            db.update_all_channels_name(number_group_parser, new_channels_name)
                        elif channel_name[-1] == "❌":
                            group_index = channels_parser.index(channel_name)
                            all_channels_name_parser = db.select_channels_name_with_number(number_group_parser)
                            group_name = all_channels_name_parser[group_index]
                            all_channels = db.select_channels_with_number(number_group_parser)
                            new_callback = channel_name[:-1] + "✅"
                            new_channels = [new_callback if item == channel_name else item for item in all_channels]
                            db.update_all_channels(number_group_parser, new_channels)
                            new_callback_name = group_name[:-1] + "✅"
                            new_channels_name = [new_callback_name if item == group_name else item for item in all_channels_name_parser]
                            db.update_all_channels_name(number_group_parser, new_channels_name)
                        elif channel_name[-1] == "⏳":
                            await callback_query.answer(cfg.error_dostup_chat, show_alert=True)
                        channels = db.select_channels_with_number(number_group_parser)
                        channels_name_parser = db.select_channels_name_with_number(number_group_parser)
                        markup_inline = types.InlineKeyboardMarkup(row_width=2)
                        paired_channels = zip(channels_name_parser[from_page_parser:before_page_parser], channels[from_page_parser:before_page_parser])
                        for channel_name, channel in paired_channels:
                            button = types.InlineKeyboardButton(text=channel_name, callback_data=channel)
                            markup_inline.row(button)
                        buttons_count = types.InlineKeyboardButton(
                            text=f"Страница {page_here_parser}/{channels_page_parser} 📄", callback_data="page_parser")
                        markup_inline.add(buttons_count)
                        if channels_count_all_parser > 10:
                            buttons_next = types.InlineKeyboardButton(text=cfg.next_page, callback_data="next_page_parser")
                            buttons_old = types.InlineKeyboardButton(text=cfg.old_page, callback_data="old_page_parser")
                            markup_inline.row(buttons_old, buttons_next)
                        if db.check_date_tarife_for_number(number_group_parser) is None:
                            pay_money_buttons = types.InlineKeyboardButton(text=cfg.pay_money_channels, callback_data='pay_money_channels_parser')
                            markup_inline.add(pay_money_buttons)
                        change_keywords = types.InlineKeyboardButton(text=cfg.change_keyword_button, callback_data='change_keyword_parser')
                        back_channels = types.InlineKeyboardButton(text=cfg.back_channels, callback_data='back_channels_parser')
                        markup_inline.add(change_keywords)
                        markup_inline.add(back_channels)
                        await callback_query.message.edit_caption(caption=cfg.group_text_use, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
            elif callback_query.data == "next_page_parser":
                if channels_page_parser == page_here_parser:
                    await callback_query.answer(cfg.error_page_next, show_alert=True)
                else:
                    channels = db.select_channels_with_number(number_group_parser)
                    channels_name_parser = db.select_channels_name_with_number(number_group_parser)
                    markup_inline = types.InlineKeyboardMarkup(row_width=2)
                    page_here_parser = page_here_parser + 1
                    await state.update_data(page_here_parser=page_here_parser)
                    await state.update_data(channels_count_parser=channels_count_parser)
                    from_page_parser = from_page_parser + 10
                    before_page_parser = before_page_parser + 10
                    await state.update_data(from_page_parser=from_page_parser)
                    await state.update_data(before_page_parser=before_page_parser)
                    paired_channels = zip(channels_name_parser[from_page_parser:before_page_parser], channels[from_page_parser:before_page_parser])
                    for channel_name, channel in paired_channels:
                        button = types.InlineKeyboardButton(text=channel_name, callback_data=channel)
                        markup_inline.row(button)
                    buttons_count = types.InlineKeyboardButton(text=f"Страница {page_here_parser}/{channels_page_parser} 📄", callback_data="page_parser")
                    markup_inline.add(buttons_count)
                    if channels_count_all_parser > 10:
                        buttons_next = types.InlineKeyboardButton(text=cfg.next_page, callback_data="next_page_parser")
                        buttons_old = types.InlineKeyboardButton(text=cfg.old_page, callback_data="old_page_parser")
                        markup_inline.row(buttons_old, buttons_next)
                    if db.check_date_tarife_for_number(number_group_parser) is None:
                        pay_money_buttons = types.InlineKeyboardButton(text=cfg.pay_money_channels, callback_data='pay_money_channels_parser')
                        markup_inline.add(pay_money_buttons)
                    change_keywords = types.InlineKeyboardButton(text=cfg.change_keyword_button, callback_data='change_keyword_parser')
                    back_channels = types.InlineKeyboardButton(text=cfg.back_channels, callback_data='back_channels_parser')
                    markup_inline.add(change_keywords)
                    markup_inline.add(back_channels)
                    await callback_query.message.edit_caption(caption=cfg.group_text_use, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
            elif callback_query.data == "old_page_parser":
                print(f"{channels_count_parser}\n{page_here_parser}\n{from_page_parser}\n{before_page_parser}")
                if page_here_parser == 1:
                    await callback_query.answer(cfg.error_page_old, show_alert=True)
                else:
                    channels = db.select_channels_with_number(number_group_parser)
                    channels_name_parser = db.select_channels_name_with_number(number_group_parser)
                    markup_inline = types.InlineKeyboardMarkup(row_width=2)
                    page_here_parser = page_here_parser - 1
                    before_page_parser = before_page_parser - 10
                    from_page_parser = from_page_parser - 10
                    await state.update_data(from_page_parser=from_page_parser)
                    await state.update_data(before_page_parser=before_page_parser)
                    await state.update_data(page_here_parser=page_here_parser)
                    await state.update_data(channels_count_parser=channels_count_parser)
                    paired_channels = zip(channels_name_parser[from_page_parser:before_page_parser], channels[from_page_parser:before_page_parser])
                    for channel_name, channel in paired_channels:
                        button = types.InlineKeyboardButton(text=channel_name, callback_data=channel)
                        markup_inline.row(button)
                    buttons_count = types.InlineKeyboardButton(text=f"Страница {page_here_parser}/{channels_page_parser} 📄", callback_data="page_parser")
                    markup_inline.add(buttons_count)
                    if channels_count_all_parser > 10:
                        buttons_next = types.InlineKeyboardButton(text=cfg.next_page, callback_data="next_page_parser")
                        buttons_old = types.InlineKeyboardButton(text=cfg.old_page, callback_data="old_page_parser")
                        markup_inline.row(buttons_old, buttons_next)
                    if db.check_date_tarife_for_number(number_group_parser) is None:
                        pay_money_buttons = types.InlineKeyboardButton(text=cfg.pay_money_channels, callback_data='pay_money_channels_parser')
                        markup_inline.add(pay_money_buttons)
                    change_keywords = types.InlineKeyboardButton(text=cfg.change_keyword_button,
                                                                 callback_data='change_keyword_parser')
                    back_channels = types.InlineKeyboardButton(text=cfg.back_channels, callback_data='back_channels_parser')
                    markup_inline.add(change_keywords)
                    markup_inline.add(back_channels)
                    await callback_query.message.edit_caption(caption=cfg.group_text_use, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
            elif callback_query.data == "back_channels_parser":
                markup_inline = types.InlineKeyboardMarkup(row_width=1)
                group_names = db.select_group_name(user_id)
                max_buttons = 5
                for i in range(min(max_buttons, len(group_names))):
                    button = types.InlineKeyboardButton(text=group_names[i], callback_data=group_names[i])
                    markup_inline.add(button)
                btn_inline1 = types.InlineKeyboardButton(cfg.groups_add_button, callback_data='groups_add_button_parser')
                markup_inline.add(btn_inline1)
                await callback_query.message.edit_caption(caption=cfg.parser_text, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
            elif callback_query.data == "pay_money_channels_parser":
                markup_inline = types.InlineKeyboardMarkup(row_width=1)
                btn_inline1 = types.InlineKeyboardButton(cfg.confirm_oplata, callback_data='confirm_oplata_parser')
                btn_inline2 = types.InlineKeyboardButton(cfg.back_button, callback_data='back_oplata_parser')
                markup_inline.add(btn_inline1, btn_inline2)
                channels_len = len(channels_parser)
                money_oplata = str(5 * int(channels_len))
                await callback_query.message.edit_caption(caption=cfg.oplata_chatov(channels_len, money_oplata), reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
            elif callback_query.data == "confirm_oplata_parser":
                balance = db.check_balance(user_id)
                channels_len = len(channels_parser)
                money_oplata = 5 * int(channels_len)
                if balance >= money_oplata:
                    await callback_query.message.answer(cfg.confirm_oplata_text)
                    channels = db.select_channels_with_number(number_group_parser)
                    new_channels = [newer[:-2] + " ✅" for newer in channels]
                    new_chan = [newer[:-2] for newer in channels]
                    db.update_all_channels(number_group_parser, new_channels)
                    channels_name_parser = db.select_channels_name_with_number(number_group_parser)
                    new_channels_name = [newer[:-2] + " ✅" for newer in channels_name_parser]
                    db.update_all_channels_name(number_group_parser, new_channels_name)
                    db.update_balance(user_id, money_oplata)
                    channels_len = len(channels)
                    current_data = datetime.datetime.now()
                    new_date = current_data + datetime.timedelta(days=30)
                    formatted_date_new = new_date.strftime("%Y-%m-%d %H:%M:%S")
                    db.add_date_tariffe(user_id, formatted_date_new, number_group_parser)
                    markup_inline = types.InlineKeyboardMarkup(row_width=1)
                    btn_inline1 = types.InlineKeyboardButton(cfg.menu_button, callback_data='menu_after_pay_parser')
                    markup_inline.add(btn_inline1)
                    all_channels = db.select_channels_with_number(number_group_parser)
                    all_channels_name = db.select_channels_name_with_number(number_group_parser)
                    updated_a = [x[:-1] + '⏳' if len(x) >= 13 and x[13] == '+' else x for x in all_channels]
                    db.update_all_channels(number_group_parser, updated_a)
                    paired_channels = zip(updated_a, all_channels_name)
                    for channel_name_updated, channel_name_id in paired_channels:
                        if channel_name_updated[13] == "+":
                            response = requests.get(channel_name_updated[:-2])
                            html_content = response.text
                            soup = BeautifulSoup(html_content, 'html.parser')
                            title_div = soup.find('div', {'class': 'tgme_page_title'})
                            if title_div:
                                group_name = title_div.get_text(strip=True)
                                all_channels_name_parser = db.select_channels_name_with_number(number_group_parser)
                                new_callback_name = group_name + '⏳'
                                new_channels_name = [new_callback_name if item[:-2] == group_name else item for item in all_channels_name_parser]
                                db.update_all_channels_name(number_group_parser, new_channels_name)
                    channels_id = db.select_channels_id_parser()
                    print(channels_id)
                    all_channels = db.select_channels_with_number(number_group_parser)
                    channels_link = [item for item in all_channels if len(item) >= 13 and item[13] == '+']
                    new_lst_id = []
                    new_lst_with_id = []
                    channels_id = [item for sublist in channels_id if sublist[0] for item in sublist[0]]
                    print(channels_id)
                    if channels_id != [(None,)]:
                        for channel_id in channels_id:
                            for channel_link in channels_link:
                                index = 0
                                if channel_id[1] == channel_link[:-2]:
                                    lst_id = [f"{index}) {channel_id}", channel_link[:-2]]
                                    lst_with_id = [f"{index}) {channel_id}"]
                                    new_lst_with_id.append(lst_with_id)
                                    new_lst_id.append(lst_id)
                                index += 1
                    new_lst = []
                    if channels_id != []:
                        for new_lst_with_ids in new_lst_with_id:
                            new_lst.append(new_lst_with_ids)
                            all_channels = db.select_channels_with_number(number_group_parser)
                            channels_link = [item for item in all_channels if len(item) >= 13 and item[13] == '+']
                            index = int(new_lst_with_ids[0]) - 1
                            channels_link[index] = channels_link[index].replace("⏳", "✅")
                            owner_lst = [next((full_word for full_word in channels_link if full_word[:-2] == word[:-2]), word) for word in all_channels]
                            db.update_all_channels(number_group_parser, owner_lst)
                        all_channels = db.select_channels_with_number(number_group_parser)
                        for channel_name in all_channels:
                            if channel_name[-1] == "✅":
                                index_channel = all_channels.index(channel_name)
                                all_channels_name = db.select_channels_name_with_number(number_group_parser)
                                group_name = all_channels_name[index_channel]
                                new_callback_name = group_name[:-1] + "✅"
                                new_channels_name = [new_callback_name if item == group_name else item for item in all_channels_name]
                                db.update_all_channels_name(number_group_parser, new_channels_name)
                    await check_private_channel(new_chan, user_id, number_group_parser)
                    await state.finish()
                    await callback_query.message.delete()
                    await callback_query.message.answer(text=cfg.tariffe_correct(group_name_parser, channels_len, formatted_date_new), reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
                else:
                    await callback_query.answer(text=cfg.tariffe_error, show_alert=True)
            elif callback_query.data == "back_oplata_parser":
                channels = db.select_channels_with_number(number_group_parser)
                channels_name_parser = db.select_channels_name_with_number(number_group_parser)
                markup_inline = types.InlineKeyboardMarkup(row_width=2)
                paired_channels = zip(channels_name_parser[from_page_parser:before_page_parser], channels[from_page_parser:before_page_parser])
                for channel_name, channel in paired_channels:
                    button = types.InlineKeyboardButton(text=channel_name, callback_data=channel)
                    markup_inline.row(button)
                buttons_count = types.InlineKeyboardButton(text=f"Страница {page_here_parser}/{channels_page_parser} 📄", callback_data="page_parser")
                markup_inline.add(buttons_count)
                if channels_count_all_parser > 10:
                    buttons_next = types.InlineKeyboardButton(text=cfg.next_page, callback_data="next_page_parser")
                    buttons_old = types.InlineKeyboardButton(text=cfg.old_page, callback_data="old_page_parser")
                    markup_inline.row(buttons_old, buttons_next)
                if db.check_date_tarife_for_number(number_group_parser) is None:
                    pay_money_buttons = types.InlineKeyboardButton(text=cfg.pay_money_channels, callback_data='pay_money_channels_parser')
                    markup_inline.add(pay_money_buttons)
                change_keywords = types.InlineKeyboardButton(text=cfg.change_keyword_button, callback_data='change_keyword_parser')
                back_channels = types.InlineKeyboardButton(text=cfg.back_channels, callback_data='back_channels_parser')
                markup_inline.add(change_keywords)
                markup_inline.add(back_channels)
                await callback_query.message.edit_caption(caption=cfg.group_text_use, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
            elif callback_query.data == "change_keyword_parser":
                markup_reply= types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
                markup_reply.add(cfg.cancel_button)
                await state.update_data(number_group=number_group_parser)
                await callback_query.message.answer(cfg.change_keyword_text, reply_markup=markup_reply)
                await Change_keyword.change_keyword_1.set()
        try:
            data = await state.get_data()
            number_group_autoposting = data.get('number_post_autoposting')
            if number_group_autoposting is not None:
                channels_autoposting = db.select_chats_account_with_number(number_group_autoposting)
                check_tarife_autoposting = db.check_date_tarife_account_for_number(number_group_autoposting)
                group_name_autoposting = db.select_account_name_for_number_group(number_group_autoposting)
                channels_count_all_autoposting = len(channels_autoposting)
                channels_count_autoposting = data.get("channels_count_autoposting")
                channels_page_autoposting = data.get("channels_page_autoposting")
                page_here_autoposting = data.get("page_here_autoposting")
                from_page_autoposting = data.get("from_page_autoposting")
                before_page_autoposting = data.get("before_page_autoposting")
                all_times = [f'{hour:02d}:{minute:02d}' for hour in range(24) for minute in range(60)]
                if callback_query.data in channels_autoposting:
                    if check_tarife_autoposting is None:
                        await callback_query.answer(text=cfg.error_oplata, show_alert=True)
                    else:
                        current_data = datetime.datetime.now()
                        formated_check_date_tarife = datetime.datetime.strptime(check_tarife_autoposting, "%Y-%m-%d %H:%M:%S")
                        if current_data >= formated_check_date_tarife:
                            db.delete_old_tariffe(user_id, number_group_autoposting)
                            await callback_query.answer(text=cfg.error_oplata, show_alert=True)
                        else:
                            channel_name = callback_query.data
                            if channel_name[-1] == "⏳":
                                await callback_query.answer(cfg.error_dostup_chat, show_alert=True)
                            else:
                                markup_inline = types.InlineKeyboardMarkup(row_width=1)
                                post_names = db.select_chats_account_with_number_autoposting(number_group_autoposting)
                                selected_sublist = [sublist for sublist in post_names if sublist[0] == channel_name]
                                result = selected_sublist[0] if selected_sublist else []
                                times = [datetime_str.split()[1][:5] for datetime_str in result[1:]]
                                for time in times:
                                    button = types.InlineKeyboardButton(text=time, callback_data=time)
                                    markup_inline.add(button)
                                if channel_name[-1] == "✅":
                                    markup_inline.add(types.InlineKeyboardButton(text=cfg.off_chat_button, callback_data="off_chat_autoposting"))
                                elif channel_name[-1] == "❌":
                                    markup_inline.add(types.InlineKeyboardButton(text=cfg.on_chat_button, callback_data="on_chat_autoposting"))
                                markup_inline.add(
                                    types.InlineKeyboardButton(text=cfg.add_time_button, callback_data="add_time_autoposting_chat"),
                                    types.InlineKeyboardButton(text=cfg.back_button, callback_data="back_settings_chat_time_autoposting")
                                )
                                await state.update_data(settings_callback_data=channel_name)
                                await state.update_data(number_group_autoposting=number_group_autoposting)
                                await callback_query.message.edit_caption(caption=cfg.time_chats_autoposting_text, reply_markup=markup_inline)
                elif callback_query.data == "back_settings_chat_time_autoposting":
                    channels = db.select_chats_account_with_number(number_group_autoposting)
                    channels_name = db.select_chats_name_account_with_number(number_group_autoposting)
                    markup_inline = types.InlineKeyboardMarkup(row_width=1)
                    paired_channels = zip(channels_name[from_page_autoposting:before_page_autoposting], channels[from_page_autoposting:before_page_autoposting])
                    for channel_name, channel in paired_channels:
                        buttons = types.InlineKeyboardButton(text=channel_name, callback_data=channel)
                        markup_inline.row(buttons)
                    buttons_count = types.InlineKeyboardButton(
                        text=f"Страница {page_here_autoposting}/{channels_page_autoposting} 📄",
                        callback_data="page_autoposting")
                    markup_inline.add(buttons_count)
                    if channels_count_all_autoposting > 10:
                        buttons_next = types.InlineKeyboardButton(text=cfg.next_page, callback_data="next_page_autoposting")
                        buttons_old = types.InlineKeyboardButton(text=cfg.old_page, callback_data="old_page_autoposting")
                        markup_inline.row(buttons_old, buttons_next)
                    if db.check_date_tarife_account_for_number(number_group_autoposting) is None:
                        pay_money_buttons = types.InlineKeyboardButton(text=cfg.pay_money_channels, callback_data='pay_money_channels_autoposting')
                        markup_inline.add(pay_money_buttons)
                    back_channels = types.InlineKeyboardButton(text=cfg.back_channels, callback_data='back_channels_autoposting')
                    delete_post_button = types.InlineKeyboardButton(text=cfg.delete_post_button, callback_data="delete_post_autoposting")
                    markup_inline.add(delete_post_button, back_channels)
                    await callback_query.message.edit_caption(caption=cfg.account_text_use, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
                elif callback_query.data == "add_time_autoposting_chat":
                    data = await state.get_data()
                    settings_callback_data = data.get("settings_callback_data")
                    await state.update_data(number_group_autoposting=number_group_autoposting)
                    post_names = db.select_chats_account_with_number_autoposting(number_group_autoposting)
                    selected_sublist = [sublist for sublist in post_names if sublist[0] == settings_callback_data]
                    result = selected_sublist[0] if selected_sublist else []
                    times = [datetime_str.split()[1][:5] for datetime_str in result[1:]]
                    if len(times) >= 3:
                        await callback_query.answer(cfg.add_time_text_limit, show_alert=True)
                    else:
                        await Add_time_autoposting_chat.add_time_autoposting_1.set()
                        markup_reply = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
                        markup_reply.add(cfg.cancel_button)
                        await callback_query.message.answer(cfg.add_time_text, reply_markup=markup_reply)
                elif callback_query.data in all_times:
                    await state.update_data(time_for_chat=callback_query.data)
                    data = await state.get_data()
                    number_group_autoposting = data.get("number_group_autoposting")
                    await state.update_data(number_group_autoposting=number_group_autoposting)
                    markup_inline = types.InlineKeyboardMarkup(row_width=1)
                    markup_inline.add(
                        types.InlineKeyboardButton(cfg.change_time_chat_button, callback_data="change_time_chat_button_autoposting"),
                        types.InlineKeyboardButton(cfg.back_button, callback_data="back_change_time_chat_button_autoposting"),
                        types.InlineKeyboardButton(cfg.delete_time_chat_button, callback_data="delete_time_chat_button_autoposting")
                    )
                    await callback_query.message.edit_caption(cfg.time_functions_chats_text, reply_markup=markup_inline)
                elif callback_query.data == "back_change_time_chat_button_autoposting":
                    markup_inline = types.InlineKeyboardMarkup(row_width=1)
                    post_names = db.select_chats_account_with_number_autoposting(number_group_autoposting)
                    data = await state.get_data()
                    channel_name = data.get("settings_callback_data")
                    selected_sublist = [sublist for sublist in post_names if sublist[0] == channel_name]
                    result = selected_sublist[0] if selected_sublist else []
                    times = [datetime_str.split()[1][:5] for datetime_str in result[1:]]
                    for time in times:
                        button = types.InlineKeyboardButton(text=time, callback_data=time)
                        markup_inline.add(button)
                    if channel_name[-1] == "✅":
                        markup_inline.add(types.InlineKeyboardButton(text=cfg.off_chat_button, callback_data="off_chat_autoposting"))
                    elif channel_name[-1] == "❌":
                        markup_inline.add(types.InlineKeyboardButton(text=cfg.on_chat_button, callback_data="on_chat_autoposting"))
                    markup_inline.add(
                        types.InlineKeyboardButton(text=cfg.add_time_button, callback_data="add_time_autoposting_chat"),
                        types.InlineKeyboardButton(text=cfg.back_button, callback_data="back_settings_chat_time_autoposting")
                    )
                    await callback_query.message.edit_caption(caption=cfg.time_chats_autoposting_text, reply_markup=markup_inline)
                elif callback_query.data == "on_chat_autoposting":
                    data = await state.get_data()
                    settings_callback_data = data.get("settings_callback_data")
                    chat_idln = db.select_chats_account_with_number_autoposting(number_group_autoposting)
                    selected_sublist = [sublist for sublist in chat_idln if sublist[0] == settings_callback_data]
                    if len(selected_sublist[0]) > 1:
                        b_replaced = settings_callback_data[:-1] + "✅"
                        group_index = channels_autoposting.index(settings_callback_data)
                        all_channels_name = db.select_chats_name_account_with_number(number_group_autoposting)
                        group_name = all_channels_name[group_index]
                        new_callback_name = group_name[:-1] + "✅"
                        new_channels_name = [new_callback_name if item == group_name else item for item in all_channels_name]
                        db.update_all_chats_name_account(number_group_autoposting, new_channels_name)
                        a_updated = [[b_replaced if item == settings_callback_data else item for item in sublist] for sublist in chat_idln]
                        json_data = json.dumps(a_updated)
                        db.update_chat_idn_autoposting(json_data, number_group_autoposting)
                        markup_inline = types.InlineKeyboardMarkup(row_width=1)
                        post_names = db.select_chats_account_with_number_autoposting(number_group_autoposting)
                        selected_sublist = [sublist for sublist in post_names if sublist[0] == b_replaced]
                        result = selected_sublist[0] if selected_sublist else []
                        times = [datetime_str.split()[1][:5] for datetime_str in result[1:]]
                        for time in times:
                            button = types.InlineKeyboardButton(text=time, callback_data=time)
                            markup_inline.add(button)
                        if b_replaced[-1] == "✅":
                            markup_inline.add(types.InlineKeyboardButton(text=cfg.off_chat_button, callback_data="off_chat_autoposting"))
                        elif b_replaced[-1] == "❌":
                            markup_inline.add(types.InlineKeyboardButton(text=cfg.on_chat_button, callback_data="on_chat_autoposting"))
                        markup_inline.add(
                            types.InlineKeyboardButton(text=cfg.add_time_button, callback_data="add_time_autoposting_chat"),
                            types.InlineKeyboardButton(text=cfg.back_button,callback_data="back_settings_chat_time_autoposting")
                        )
                        await state.update_data(settings_callback_data=b_replaced)
                        await callback_query.message.edit_reply_markup(reply_markup=markup_inline)
                    else:
                        await callback_query.answer(cfg.without_time_in_chat_text, show_alert=True)
                elif callback_query.data == "off_chat_autoposting":
                    data = await state.get_data()
                    settings_callback_data = data.get("settings_callback_data")
                    print(settings_callback_data)
                    chat_idln = db.select_chats_account_with_number_autoposting(number_group_autoposting)
                    b_replaced = settings_callback_data[:-1] + "❌"
                    print(b_replaced)
                    group_index = channels_autoposting.index(settings_callback_data)
                    all_channels_name = db.select_chats_name_account_with_number(number_group_autoposting)
                    group_name = all_channels_name[group_index]
                    new_callback_name = group_name[:-1] + "❌"
                    new_channels_name = [new_callback_name if item == group_name else item for item in all_channels_name]
                    db.update_all_chats_name_account(number_group_autoposting, new_channels_name)
                    a_updated = [[b_replaced if item == settings_callback_data else item for item in sublist] for sublist in chat_idln]
                    print(a_updated)
                    json_data = json.dumps(a_updated)
                    db.update_chat_idn_autoposting(json_data, number_group_autoposting)
                    markup_inline = types.InlineKeyboardMarkup(row_width=1)
                    post_names = db.select_chats_account_with_number_autoposting(number_group_autoposting)
                    selected_sublist = [sublist for sublist in post_names if sublist[0] == b_replaced]
                    result = selected_sublist[0] if selected_sublist else []
                    times = [datetime_str.split()[1][:5] for datetime_str in result[1:]]
                    for time in times:
                        button = types.InlineKeyboardButton(text=time, callback_data=time)
                        markup_inline.add(button)
                    if b_replaced[-1] == "✅":
                        markup_inline.add(types.InlineKeyboardButton(text=cfg.off_chat_button, callback_data="off_chat_autoposting"))
                    elif b_replaced[-1] == "❌":
                        markup_inline.add(types.InlineKeyboardButton(text=cfg.on_chat_button, callback_data="on_chat_autoposting"))
                    markup_inline.add(
                        types.InlineKeyboardButton(text=cfg.add_time_button, callback_data="add_time_autoposting_chat"),
                        types.InlineKeyboardButton(text=cfg.back_button, callback_data="back_settings_chat_time_autoposting")
                    )
                    await state.update_data(settings_callback_data=b_replaced)
                    await callback_query.message.edit_reply_markup(reply_markup=markup_inline)
                elif callback_query.data == "change_time_chat_button_autoposting":
                    data = await state.get_data()
                    number_group_autoposting = data.get("number_group_autoposting")
                    await state.update_data(number_group_autoposting=number_group_autoposting)
                    await Change_time_autoposting_chat.change_time_autoposting_1.set()
                    markup_reply = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
                    markup_reply.add(cfg.cancel_button)
                    await callback_query.message.answer(cfg.add_time_text, reply_markup=markup_reply)
                elif callback_query.data == "delete_time_chat_button_autoposting":
                    markup_inline = types.InlineKeyboardMarkup(row_width=1)
                    btn_yes = types.InlineKeyboardButton("Да", callback_data='yes_delete_time_autoposting')
                    btn_no = types.InlineKeyboardButton("Нет", callback_data='no_delete_time_autoposting')
                    markup_inline.add(btn_yes, btn_no)
                    await callback_query.message.edit_caption(caption=cfg.delete_time_autoposting_text, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
                elif callback_query.data == "no_delete_time_autoposting":
                    markup_inline = types.InlineKeyboardMarkup(row_width=1)
                    markup_inline.add(
                        types.InlineKeyboardButton(cfg.change_time_chat_button, callback_data="change_time_chat_button_autoposting"),
                        types.InlineKeyboardButton(cfg.back_button, callback_data="back_change_time_chat_button_autoposting"),
                        types.InlineKeyboardButton(cfg.delete_time_chat_button, callback_data="delete_time_chat_button_autoposting")
                    )
                    await callback_query.message.edit_caption(cfg.time_functions_chats_text, reply_markup=markup_inline)
                elif callback_query.data == "yes_delete_time_autoposting":
                    data = await state.get_data()
                    settings_callback_data = data.get("settings_callback_data")
                    post_names = db.select_chats_account_with_number_autoposting(number_group_autoposting)
                    time_for_chat = data.get("time_for_chat")
                    sublist = next((sub for sub in post_names if sub[0] == settings_callback_data), None)
                    a = None
                    if sublist:
                        if len(sublist) == 2:
                            updated_sublist = [sublist[0][:-1] + '❌'] + [time for time in sublist[1:] if time.split()[1][:5] != time_for_chat]
                            a = [updated_sublist if sub[0] == settings_callback_data else sub for sub in post_names]
                            group_index = channels_autoposting.index(settings_callback_data)
                            all_channels_name = db.select_chats_name_account_with_number(number_group_autoposting)
                            group_name = all_channels_name[group_index]
                            new_callback_name = group_name[:-1] + "❌"
                            new_channels_name = [new_callback_name if item == group_name else item for item in all_channels_name]
                            db.update_all_chats_name_account(number_group_autoposting, new_channels_name)
                        else:
                            updated_sublist = [sublist[0]] + [time for time in sublist[1:] if time.split()[1][:5] != time_for_chat]
                            a = [updated_sublist if sub[0] == settings_callback_data else sub for sub in post_names]
                    json_data = json.dumps(a)
                    db.update_chat_idn_autoposting(json_data, number_group_autoposting)
                    await callback_query.message.answer(cfg.delete_time_autoposting_yes_text)
                elif callback_query.data == "next_page_autoposting":
                    if channels_page_autoposting == page_here_autoposting:
                        await callback_query.answer(cfg.error_page_next, show_alert=True)
                    else:
                        channels = db.select_chats_account_with_number(number_group_autoposting)
                        channels_name = db.select_chats_name_account_with_number(number_group_autoposting)
                        markup_inline = types.InlineKeyboardMarkup(row_width=2)
                        page_here_autoposting = page_here_autoposting + 1
                        await state.update_data(page_here_autoposting=page_here_autoposting)
                        await state.update_data(channels_count_autoposting=channels_count_autoposting)
                        from_page_autoposting = from_page_autoposting + 10
                        before_page_autoposting = before_page_autoposting + 10
                        await state.update_data(from_page_autoposting=from_page_autoposting)
                        await state.update_data(before_page_autoposting=before_page_autoposting)
                        paired_channels = zip(channels_name[from_page_autoposting:before_page_autoposting], channels[from_page_autoposting:before_page_autoposting])
                        for channel_name, channel in paired_channels:
                            buttons = types.InlineKeyboardButton(text=channel_name, callback_data=channel)
                            markup_inline.row(buttons)
                        buttons_count = types.InlineKeyboardButton(
                            text=f"Страница {page_here_autoposting}/{channels_page_autoposting} 📄",
                            callback_data="page_autoposting")
                        markup_inline.add(buttons_count)
                        if channels_count_all_autoposting > 10:
                            buttons_next = types.InlineKeyboardButton(text=cfg.next_page, callback_data="next_page_autoposting")
                            buttons_old = types.InlineKeyboardButton(text=cfg.old_page, callback_data="old_page_autoposting")
                            markup_inline.row(buttons_old, buttons_next)
                        if db.check_date_tarife_account_for_number(number_group_autoposting) is None:
                            pay_money_buttons = types.InlineKeyboardButton(text=cfg.pay_money_channels, callback_data='pay_money_channels_autoposting')
                            markup_inline.add(pay_money_buttons)
                        delete_post_button = types.InlineKeyboardButton(text=cfg.delete_post_button, callback_data="delete_post_autoposting")
                        back_channels = types.InlineKeyboardButton(text=cfg.back_channels, callback_data='back_channels_autoposting')
                        markup_inline.add(delete_post_button, back_channels)
                        await callback_query.message.edit_caption(caption=cfg.account_text_use(), reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
                elif callback_query.data == "delete_post_autoposting":
                    data = await state.get_data()
                    post_name = data.get("post_name_autoposting")
                    markup_inline = types.InlineKeyboardMarkup(row_width=1)
                    btn_yes = types.InlineKeyboardButton("Да", callback_data='yes_delete_autoposting')
                    btn_no = types.InlineKeyboardButton("Нет", callback_data='no_delete_autoposting')
                    markup_inline.add(btn_yes, btn_no)
                    await callback_query.message.edit_caption(caption=cfg.delete_post_text(post_name), reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
                elif callback_query.data == "yes_delete_autoposting":
                    post_name1 = str(callback_query.message)
                    post_name2 = re.findall(r"'([^']*)'", post_name1)
                    db.delete_post(post_name2[0])
                    await callback_query.message.delete()
                    await callback_query.message.answer(text=cfg.delete_post_yes_text(post_name2[0]))
                elif callback_query.data == "no_delete_autoposting":
                    post_name1 = str(callback_query.message)
                    post_name2 = re.findall(r"'([^']*)'", post_name1)
                    channels = db.select_chats_post(user_id, str(post_name2[0]))
                    channels_name = db.select_chats_name_post(user_id, str(post_name2[0]))
                    markup_inline = types.InlineKeyboardMarkup(row_width=1)
                    channels_count_autoposting = len(channels)
                    channels_page_autoposting = fnc.get_category(channels_count_autoposting)
                    number_post_autoposting = db.select_number_post(user_id, str(post_name2[0]))
                    await state.update_data(number_post_autoposting=number_post_autoposting)
                    page_here_autoposting = 1
                    from_page_autoposting = 0
                    before_page_autoposting = 10
                    await state.update_data(channels_count_autoposting=channels_count_autoposting)
                    await state.update_data(channels_page_autoposting=channels_page_autoposting)
                    await state.update_data(page_here_autoposting=page_here_autoposting)
                    await state.update_data(from_page_autoposting=from_page_autoposting)
                    await state.update_data(before_page_autoposting=before_page_autoposting)
                    paired_channels = zip(channels_name[from_page_autoposting:before_page_autoposting], channels[from_page_autoposting:before_page_autoposting])
                    for channel_name, channel in paired_channels:
                        buttons = types.InlineKeyboardButton(text=channel_name, callback_data=channel)
                        markup_inline.row(buttons)
                    buttons_count = types.InlineKeyboardButton(
                        text=f"Страница {page_here_autoposting}/{channels_page_autoposting} 📄",
                        callback_data="page_autoposting")
                    markup_inline.add(buttons_count)
                    if channels_count_autoposting > 10:
                        buttons_next = types.InlineKeyboardButton(text=cfg.next_page, callback_data="next_page_autoposting")
                        buttons_old = types.InlineKeyboardButton(text=cfg.old_page, callback_data="old_page_autoposting")
                        markup_inline.row(buttons_old, buttons_next)
                    if db.check_date_tarife_account(user_id, str(post_name2[0])) is None:
                        pay_money_buttons = types.InlineKeyboardButton(text=cfg.pay_money_channels, callback_data='pay_money_channels_autoposting')
                        markup_inline.add(pay_money_buttons)
                    back_channels = types.InlineKeyboardButton(text=cfg.back_channels, callback_data='back_channels_autoposting')
                    delete_post_button = types.InlineKeyboardButton(text=cfg.delete_post_button, callback_data="delete_post_autoposting")
                    markup_inline.add(delete_post_button, back_channels)
                    await callback_query.message.edit_caption(caption=cfg.account_text_use, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
                elif callback_query.data == "old_page_autoposting":
                    print(
                        f"{channels_count_autoposting}\n{page_here_autoposting}\n{from_page_autoposting}\n{before_page_autoposting}")
                    if page_here_autoposting == 1:
                        await callback_query.answer(cfg.error_page_old, show_alert=True)
                    else:
                        channels = db.select_chats_account_with_number(number_group_autoposting)
                        channels_name = db.select_chats_name_account_with_number(number_group_autoposting)
                        markup_inline = types.InlineKeyboardMarkup(row_width=2)
                        page_here_autoposting = page_here_autoposting - 1
                        before_page_autoposting = before_page_autoposting - 10
                        from_page_autoposting = from_page_autoposting - 10
                        await state.update_data(from_page_autoposting=from_page_autoposting)
                        await state.update_data(before_page_autoposting=before_page_autoposting)
                        await state.update_data(page_here_autoposting=page_here_autoposting)
                        await state.update_data(channels_count_autoposting=channels_count_autoposting)
                        paired_channels = zip(channels_name[from_page_autoposting:before_page_autoposting], channels[from_page_autoposting:before_page_autoposting])
                        for channel_name, channel in paired_channels:
                            buttons = types.InlineKeyboardButton(text=channel_name, callback_data=channel)
                            markup_inline.row(buttons)
                        buttons_count = types.InlineKeyboardButton(
                            text=f"Страница {page_here_autoposting}/{channels_page_autoposting} 📄",
                            callback_data="page_autoposting")
                        markup_inline.add(buttons_count)
                        if channels_count_all_autoposting > 10:
                            buttons_next = types.InlineKeyboardButton(text=cfg.next_page, callback_data="next_page_autoposting")
                            buttons_old = types.InlineKeyboardButton(text=cfg.old_page, callback_data="old_page_autoposting")
                            markup_inline.row(buttons_old, buttons_next)
                        if db.check_date_tarife_account_for_number(number_group_autoposting) is None:
                            pay_money_buttons = types.InlineKeyboardButton(text=cfg.pay_money_channels, callback_data='pay_money_channels_autoposting')
                            markup_inline.add(pay_money_buttons)
                        delete_post_button = types.InlineKeyboardButton(text=cfg.delete_post_button, callback_data="delete_post_autoposting")
                        back_channels = types.InlineKeyboardButton(text=cfg.back_channels, callback_data='back_channels_autoposting')
                        markup_inline.add(delete_post_button, back_channels)
                        await callback_query.message.edit_caption(caption=cfg.account_text_use, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
                elif callback_query.data == "back_channels_autoposting":
                    markup_inline = types.InlineKeyboardMarkup(row_width=1)
                    user_id = callback_query.from_user.id
                    group_names = db.select_autoposting_group_name(user_id)
                    max_buttons = 5
                    for i in range(min(max_buttons, len(group_names))):
                        button = types.InlineKeyboardButton(text=group_names[i], callback_data=group_names[i])
                        markup_inline.add(button)
                    btn1_inline = types.InlineKeyboardButton(cfg.add_account_button, callback_data="add_account_autoposting")
                    markup_inline.add(btn1_inline)
                    if group_names is None:
                        text = cfg.accounts_left_text
                    else:
                        text = cfg.accounts_right_text
                    await callback_query.message.edit_caption(caption=text, reply_markup=markup_inline)
                elif callback_query.data == "pay_money_channels_autoposting":
                    markup_inline = types.InlineKeyboardMarkup(row_width=1)
                    btn_inline1 = types.InlineKeyboardButton(cfg.confirm_oplata, callback_data='confirm_oplata_autoposting')
                    btn_inline2 = types.InlineKeyboardButton(cfg.back_button, callback_data='back_oplata_autoposting')
                    markup_inline.add(btn_inline1, btn_inline2)
                    channels_len = len(channels_autoposting)
                    days = db.select_days_autoposting_post(number_group_autoposting)
                    money_oplata = str(days * 0.15 * int(channels_len))
                    await callback_query.message.edit_caption(caption=cfg.oplata_chatov_autoposting(channels_len, money_oplata, days), reply_markup=markup_inline)
                elif callback_query.data == "confirm_oplata_autoposting":
                    balance = db.check_balance(user_id)
                    channels_len = len(channels_autoposting)
                    days = db.select_days_autoposting_post(number_group_autoposting)
                    money_oplata = days * 0.15 * int(channels_len)
                    if balance >= money_oplata:
                        channels = db.select_chats_account_with_number_confirm_oplata(number_group_autoposting)
                        channels_name = db.select_chats_name_account_with_number(number_group_autoposting)
                        new_channels = [[channel[0][:-2] + " ✅"] for channel in channels]
                        new_chats_name = [newer[:-2] + " ✅" for newer in channels_name]
                        db.update_all_chats_name_account(number_group_autoposting, new_chats_name)
                        db.update_balance(user_id, money_oplata)
                        moscow_tz = pytz.timezone('Europe/Moscow')
                        channels_len = len(channels)
                        current_data = datetime.datetime.now(moscow_tz)
                        time_betw = db.select_time_betw(number_group_autoposting)
                        hours, minutes = map(int, time_betw[0].split(':'))
                        current_date = datetime.datetime.now(moscow_tz)
                        combined_datetime = current_date.replace(hour=hours, minute=minutes, second=0, microsecond=0)
                        date_betw = combined_datetime.strftime("%Y-%m-%d %H:%M:%S")
                        new_lst = []
                        new_date = current_data + datetime.timedelta(days=days)
                        formatted_date_new = new_date.strftime("%Y-%m-%d %H:%M:%S")
                        new_lst.append(date_betw)
                        for new_channel in new_channels:
                            new_channel.append(str(date_betw))
                        json_data = json.dumps(new_channels)
                        db.update_all_chats_account(number_group_autoposting, json_data)
                        db.add_date_tariffe_autoposting(user_id, formatted_date_new, number_group_autoposting)
                        markup_inline = types.InlineKeyboardMarkup(row_width=1)
                        btn_inline1 = types.InlineKeyboardButton(cfg.menu_button, callback_data='menu_after_pay_autoposting')
                        markup_inline.add(btn_inline1)
                        await callback_query.message.delete()
                        await callback_query.message.answer(text=cfg.tariffe_correct_autoposting(group_name_autoposting, channels_len, formatted_date_new), reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
                    else:
                        await callback_query.answer(text=cfg.tariffe_error, show_alert=True)
                elif callback_query.data == "back_oplata_autoposting":
                    channels = db.select_chats_account_with_number(number_group_autoposting)
                    channels_name = db.select_chats_name_account_with_number(number_group_autoposting)
                    markup_inline = types.InlineKeyboardMarkup(row_width=1)
                    paired_channels = zip(channels_name[from_page_autoposting:before_page_autoposting], channels[from_page_autoposting:before_page_autoposting])
                    for channel_name, channel in paired_channels:
                        buttons = types.InlineKeyboardButton(text=channel_name, callback_data=channel)
                        markup_inline.row(buttons)
                    buttons_count = types.InlineKeyboardButton(
                        text=f"Страница {page_here_autoposting}/{channels_page_autoposting} 📄",
                        callback_data="page_autoposting")
                    markup_inline.add(buttons_count)
                    if channels_count_all_autoposting > 10:
                        buttons_next = types.InlineKeyboardButton(text=cfg.next_page, callback_data="next_page_autoposting")
                        buttons_old = types.InlineKeyboardButton(text=cfg.old_page, callback_data="old_page_autoposting")
                        markup_inline.row(buttons_old, buttons_next)
                    if db.check_date_tarife_account_for_number(number_group_autoposting) is None:
                        pay_money_buttons = types.InlineKeyboardButton(text=cfg.pay_money_channels, callback_data='pay_money_channels_autoposting')
                        markup_inline.add(pay_money_buttons)
                    back_channels = types.InlineKeyboardButton(text=cfg.back_channels, callback_data='back_channels_autoposting')
                    delete_post_button = types.InlineKeyboardButton(text=cfg.delete_post_button, callback_data="delete_post_autoposting")
                    markup_inline.add(delete_post_button, back_channels)
                    await callback_query.message.edit_caption(caption=cfg.account_text_use, reply_markup=markup_inline, parse_mode=types.ParseMode.MARKDOWN)
                elif callback_query.data == "change_time_betw_autoposting":
                    markup_reply_time = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
                    markup_reply_time.add(cfg.cancel_button)
                    await callback_query.message.answer(cfg.change_time_betw_text, reply_markup=markup_reply_time)
                    await Change_time_betw.change_time_betw_1.set()
        except Exception:
            await callback_query.answer("Произошла ошибка при использовании автопостинга, пожалуйста нажмите на нижнюю кнопку 'Автопостинг' и повторите попытку.", show_alert=True)

@dp.message_handler(state=Change_time_autoposting_chat.change_time_autoposting_1)
async def change_time_autoposting_1_text(message: types.Message, state: FSMContext):
    if message.chat.type == types.ChatType.PRIVATE:
        try:
            if message.text == "/cancel":
                user_id = message.from_user.id
                first_name = message.from_user.first_name
                username = message.from_user.username
                if (not db.check_user(user_id)):
                    db.add_user(user_id, first_name, username)
                markup_reply = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
                markup_reply.add(cfg.autoposting)
                markup_reply.add(cfg.parser)
                markup_reply.row(cfg.my_profile, cfg.support)
                if db.select_admin(user_id) > 0:
                    markup_reply.add(cfg.admin_panel_button)
                await message.answer(cfg.cancel_sostoyanie, parse_mode=types.ParseMode.MARKDOWN, reply_markup=markup_reply)
                await state.reset_state()
            elif message.text == cfg.cancel_button:
                user_id = message.from_user.id
                first_name = message.from_user.first_name
                username = message.from_user.username
                if (not db.check_user(user_id)):
                    db.add_user(user_id, first_name, username)
                markup_reply = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
                markup_reply.add(cfg.autoposting)
                markup_reply.add(cfg.parser)
                markup_reply.row(cfg.my_profile, cfg.support)
                if db.select_admin(user_id) > 0:
                    markup_reply.add(cfg.admin_panel_button)
                await message.answer(cfg.cancel_sostoyanie, parse_mode=types.ParseMode.MARKDOWN, reply_markup=markup_reply)
                await state.reset_state()
            else:
                hours, minutes = message.text.split(":")
                hours = int(hours)
                minutes = int(minutes)
                if 0 <= hours < 24:
                    if 0 <= minutes < 60:
                        if validate_time_format(message.text):
                            data = await state.get_data()
                            number_group_autoposting = data.get("number_group_autoposting")
                            settings_callback_data = data.get("settings_callback_data")
                            time_for_chat = data.get("time_for_chat")
                            post_names = db.select_chats_account_with_number_autoposting(number_group_autoposting)
                            selected_sublist_time = [sublist for sublist in post_names if sublist[0] == settings_callback_data]
                            result_ = selected_sublist_time[0] if selected_sublist_time else []
                            times = [datetime_str.split()[1][:5] for datetime_str in result_[1:]]
                            if message.text in times:
                                await message.answer(cfg.time_again_no_text)
                            else:
                                user_id = message.from_user.id
                                first_name = message.from_user.first_name
                                username = message.from_user.username
                                if (not db.check_user(user_id)):
                                    db.add_user(user_id, first_name, username)
                                markup_reply = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
                                markup_reply.add(cfg.autoposting)
                                markup_reply.add(cfg.parser)
                                markup_reply.row(cfg.my_profile, cfg.support)
                                if db.select_admin(user_id) > 0:
                                    markup_reply.add(cfg.admin_panel_button)
                                updated_a = [
                                    [sublist[0]] + [
                                        datetime_str.replace(time_for_chat, message.text) if datetime.datetime.strptime(datetime_str,"%Y-%m-%d %H:%M:%S").strftime("%H:%M") == time_for_chat else datetime_str
                                        for datetime_str in sublist[1:]
                                    ] if sublist[0] == settings_callback_data else sublist
                                    for sublist in post_names
                                ]
                                json_data = json.dumps(updated_a)
                                db.update_chat_idn_autoposting(json_data, number_group_autoposting)
                                await message.answer(cfg.edit_time_text_finish, reply_markup=markup_reply)
                                await state.finish()
                        else:
                            await message.answer("Формат времени не верный, отправьте время в следющем формате\b[час:минута] (Пример: 12:30)")
                    else:
                        await message.answer("Вы можете поставить минуты не больше 60 и не меньше 0, попробуйте ещё раз:")
                else:
                    await message.answer("Вы можете поставить часы не больше 23 и не меньше 0, попробуйте ещё раз:")
        except Exception:
            await message.answer("Произошла ошибка, пожалуйста повторите ещё раз:")

@dp.message_handler(state=Add_time_autoposting_chat.add_time_autoposting_1)
async def add_time_autoposting_chat_text(message: types.Message, state: FSMContext):
    if message.chat.type == types.ChatType.PRIVATE:
        try:
            if message.text == "/cancel":
                user_id = message.from_user.id
                first_name = message.from_user.first_name
                username = message.from_user.username
                if (not db.check_user(user_id)):
                    db.add_user(user_id, first_name, username)
                markup_reply = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
                markup_reply.add(cfg.autoposting)
                markup_reply.add(cfg.parser)
                markup_reply.row(cfg.my_profile, cfg.support)
                if db.select_admin(user_id) > 0:
                    markup_reply.add(cfg.admin_panel_button)
                await message.answer(cfg.cancel_sostoyanie, parse_mode=types.ParseMode.MARKDOWN, reply_markup=markup_reply)
                await state.reset_state()
            elif message.text == cfg.cancel_button:
                user_id = message.from_user.id
                first_name = message.from_user.first_name
                username = message.from_user.username
                if (not db.check_user(user_id)):
                    db.add_user(user_id, first_name, username)
                markup_reply = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
                markup_reply.add(cfg.autoposting)
                markup_reply.add(cfg.parser)
                markup_reply.row(cfg.my_profile, cfg.support)
                if db.select_admin(user_id) > 0:
                    markup_reply.add(cfg.admin_panel_button)
                await message.answer(cfg.cancel_sostoyanie, parse_mode=types.ParseMode.MARKDOWN, reply_markup=markup_reply)
                await state.reset_state()
            else:
                hours, minutes = message.text.split(":")
                hours = int(hours)
                minutes = int(minutes)
                if 0 <= hours < 24:
                    if 0 <= minutes < 60:
                        if validate_time_format(message.text):
                            data = await state.get_data()
                            number_group_autoposting = data.get("number_group_autoposting")
                            settings_callback_data = data.get("settings_callback_data")
                            post_names = db.select_chats_account_with_number_autoposting(number_group_autoposting)
                            selected_sublist_time = [sublist for sublist in post_names if sublist[0] == settings_callback_data]
                            result = selected_sublist_time[0] if selected_sublist_time else []
                            times = [datetime_str.split()[1][:5] for datetime_str in result[1:]]
                            if message.text in times:
                                await message.answer(cfg.time_again_no_text)
                            else:
                                user_id = message.from_user.id
                                first_name = message.from_user.first_name
                                username = message.from_user.username
                                if (not db.check_user(user_id)):
                                    db.add_user(user_id, first_name, username)
                                markup_reply = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
                                markup_reply.add(cfg.autoposting)
                                markup_reply.add(cfg.parser)
                                markup_reply.row(cfg.my_profile, cfg.support)
                                if db.select_admin(user_id) > 0:
                                    markup_reply.add(cfg.admin_panel_button)
                                moscow_tz = pytz.timezone('Europe/Moscow')
                                current_date = datetime.datetime.now(moscow_tz)
                                combined_datetime = current_date.replace(hour=hours, minute=minutes, second=0, microsecond=0)
                                formatted_datetime = combined_datetime.strftime("%Y-%m-%d %H:%M:%S")
                                selected_sublist = [sublist for sublist in post_names if sublist[0] == settings_callback_data]
                                result = selected_sublist[0] if selected_sublist else []
                                result.append(formatted_datetime)
                                new_updates = [result if item[0] == settings_callback_data else item for item in post_names]
                                json_data = json.dumps(new_updates)
                                db.update_chat_idn_autoposting(json_data, number_group_autoposting)
                                await message.answer(cfg.add_time_text_finish, reply_markup=markup_reply)
                                await state.finish()
                        else:
                            await message.answer("Формат времени не верный, отправьте время в следющем формате\b[час:минута] (Пример: 12:30)")
                    else:
                        await message.answer("Вы можете поставить минуты не больше 60 и не меньше 0, попробуйте ещё раз:")
                else:
                    await message.answer("Вы можете поставить часы не больше 23 и не меньше 0, попробуйте ещё раз:")
        except Exception:
            await message.answer("Произошла ошибка, возможно вы не правильно ввели, повторите ещё раз:")


@dp.message_handler(state=Change_time_betw.change_time_betw_1)
async def change_time_betw_1_func(message: types.Message, state: FSMContext):
    if message.chat.type == types.ChatType.PRIVATE:
        try:
            textsing = message.text
            text_lines = textsing.strip().split('\n')
            if message.text == "/cancel":
                await message.answer(cfg.cancel_sostoyanie, parse_mode=types.ParseMode.MARKDOWN)
                await state.reset_state()
            else:
                if 1 <= len(text_lines) <= 5:
                    try:
                        bluable = False
                        for text_lin in text_lines:
                            hours, minutes = text_lin.split(":")
                            hours = int(hours)
                            minutes = int(minutes)
                            if 0 <= hours < 24:
                                if 0 <= minutes < 61:
                                    if validate_time_format(text_lin):
                                        await Add_post.add_post_3.set()
                                        await message.answer(cfg.create_account_post_3)
                                        bluable = True
                                        current_date = datetime.datetime.now()
                                        combined_datetime = current_date.replace(hour=hours, minute=minutes, second=0, microsecond=0)
                                        formatted_datetime = combined_datetime.strftime("%Y-%m-%d %H:%M:%S")
                                        new_lst = []
                                        new_lst.append(formatted_datetime)
                                    else:
                                        await message.answer("Формат времени не верный, отправьте время в следющем формате:\n\nПример:\n10:30\n14:30")
                                        bluable = False
                                        break
                                else:
                                    await message.answer("Вы можете поставить минуты не больше 60 и не меньше 0, попробуйте ещё раз:")
                                    bluable = False
                                    break
                            else:
                                await message.answer("Вы можете поставить часы не больше 23 и не меньше 0, попробуйте ещё раз:")
                                bluable = False
                                break
                        if bluable is True:
                            pass
                    except Exception:
                        pass
                else:
                    await message.answer(cfg.error_len_keyword_create, parse_mode=types.ParseMode.MARKDOWN)
        except Exception:
            await message.answer("Произошла ошибка, пожалуйста повторите ещё раз:")


@dp.message_handler(state=Add_post.add_post_1)
async def add_post_func_text_1(message: types.Message, state: FSMContext):
    if message.chat.type == types.ChatType.PRIVATE:
        try:
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
                    channel_message_id = message.forward_from_message_id if message.forward_from_message_id else None
                    channel_tag = message.forward_from_chat.username if message.forward_from_chat else None
                    message_id_bot = message.message_id
                    await state.update_data(forwarded_message_id=channel_message_id, channel_tag=channel_tag, message_id_bot=message_id_bot)
                    await message.answer(cfg.create_account_post_2)
                    await Add_post.add_post_2.set()
                else:
                    await message.answer("Вы должны переслать сообщение из канала, попробуйте ещё раз:")
        except Exception:
            await message.answer("Произошла ошибка, пожалуйста повторите ещё раз:")


@dp.message_handler(state=Add_post.add_post_2)
async def add_post_func_text_2(message: types.Message, state: FSMContext):
    if message.chat.type == types.ChatType.PRIVATE:
        try:
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
                hours, minutes = message.text.split(":")
                hours = int(hours)
                minutes = int(minutes)
                if 0 <= hours < 24:
                    if 0 <= minutes < 61:
                        if validate_time_format(message.text):
                            await Add_post.add_post_3.set()
                            await message.answer(cfg.create_account_post_3)
                            # current_date = datetime.datetime.now()
                            # combined_datetime = current_date.replace(hour=hours, minute=minutes, second=0, microsecond=0)
                            # formatted_datetime = combined_datetime.strftime("%Y-%m-%d %H:%M:%S")
                            new_lst = []
                            new_lst.append(message.text)
                            await state.update_data(time_betw=new_lst)
                        else:
                            await message.answer("Формат времени не верный, отправьте время в следющем формате")
                    else:
                        await message.answer("Вы можете поставить минуты не больше 60 и не меньше 0, попробуйте ещё раз:")
                else:
                    await message.answer("Вы можете поставить часы не больше 23 и не меньше 0, попробуйте ещё раз:")
        except Exception:
            await message.answer("Произошла ошибка, пожалуйста повторите ещё раз:")

@dp.message_handler(state=Add_post.add_post_3)
async def add_post_func_text_3(message: types.Message, state: FSMContext):
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
            try:
                days = int(message.text)
                if 1 <= days <= 30:
                    await state.update_data(days=days)
                    await message.answer(cfg.create_account_post_4)
                    await Add_post.add_post_4.set()
                else:
                    await message.answer("Вы можете написать не меньше 1 дня и не больше 30 дней, пожалуйста повторите ещё раз:")
            except Exception:
                await message.answer("Произошла ошибка, введите дни:")

@dp.message_handler(state=Add_post.add_post_4)
async def add_post_func_text_4(message: types.Message, state: FSMContext):
    if message.chat.type == types.ChatType.PRIVATE:
        try:
            user_id = message.from_user.id
            textsing = message.text
            text_line = textsing.strip().split('\n')
            text_lines = [[element + ' ⚠'] for element in text_line]
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
                    if 1 <= len(text_lines) <= 10:
                        try:
                            channels_name_1 = []
                            await message.answer(cfg.please_wait_add_channels_name)
                            for channel_name in text_line:
                                if channel_name[13] == "+":
                                    response = requests.get(channel_name)
                                    html_content = response.text
                                    soup = BeautifulSoup(html_content, 'html.parser')
                                    title_div = soup.find('div', {'class': 'tgme_page_title'})
                                    if title_div:
                                        group_name = title_div.get_text(strip=True)
                                        channels_name_1.append(group_name)
                                    else:
                                        await message.answer(cfg.error_channel_name_add)
                                        break
                                elif channel_name[0] == "@":
                                    response = requests.get(f"https://t.me/{channel_name[1:]}")
                                    html_content = response.text
                                    soup = BeautifulSoup(html_content, 'html.parser')
                                    title_div = soup.find('div', {'class': 'tgme_page_title'})
                                    if title_div:
                                        group_name = title_div.get_text(strip=True)
                                        channels_name_1.append(group_name)
                                    else:
                                        await message.answer(cfg.error_channel_name_add)
                                        break
                                else:
                                    if channel_name[:8] == "https://":
                                        response = requests.get(channel_name)
                                    else:
                                        response = requests.get(f"https://t.me/{channel_name}")
                                    html_content = response.text
                                    soup = BeautifulSoup(html_content, 'html.parser')
                                    title_div = soup.find('div', {'class': 'tgme_page_title'})
                                    if title_div:
                                        group_name = title_div.get_text(strip=True)
                                        channels_name_1.append(group_name)
                                    else:
                                        await message.answer(cfg.error_channel_name_add)
                                        break
                            if len(channels_name_1) == len(text_line):
                                channels_name_2 = list(dict.fromkeys([element + ' ⚠' for element in channels_name_1]))
                                check_number_post = db.check_numbers_account_post()
                                new_number_post = check_number_post + 1
                                data = await state.get_data()
                                number_account = data.get("number_account")
                                string_session = db.get_string_session(number_account)
                                time_betw = data.get("time_betw")
                                forwarded_message_id = data.get("forwarded_message_id")
                                channel_tag = data.get("channel_tag")
                                message_id_bot = data.get("message_id_bot")
                                days = data.get("days")
                                json_data = json.dumps(text_lines)
                                db.add_post_account(user_id, forwarded_message_id, string_session, json_data, time_betw, new_number_post, number_account, channel_tag, message_id_bot, channels_name_2, days)
                                markup_reply = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
                                markup_reply.add(cfg.autoposting)
                                markup_reply.add(cfg.parser)
                                markup_reply.row(cfg.my_profile, cfg.support)
                                if db.select_admin(user_id) > 0:
                                    markup_reply.add(cfg.admin_panel_button)
                                await message.answer(cfg.right_create_post, reply_markup=markup_reply, parse_mode=types.ParseMode.MARKDOWN)
                                await state.finish()
                        except Exception as es:
                            await state.reset_state()
                            markup_reply = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
                            markup_reply.add(cfg.autoposting)
                            markup_reply.add(cfg.parser)
                            markup_reply.row(cfg.my_profile, cfg.support)
                            if db.select_admin(user_id) > 0:
                                markup_reply.add(cfg.admin_panel_button)
                            await message.answer(cfg.error_create_post, reply_markup=markup_reply, parse_mode=types.ParseMode.MARKDOWN)
                            print(f"[ERROR] {es}")
                    else:
                        await message.answer(cfg.error_len_chat_post_create, parse_mode=types.ParseMode.MARKDOWN)
                else:
                    await message.answer(cfg.error_len_channels, parse_mode=types.ParseMode.MARKDOWN)
        except Exception:
            await message.answer("Произошла ошибка, пожалуйста повторите ещё раз:")

@dp.message_handler(state=Change_keyword.change_keyword_1)
async def change_keyword_1_func(message: types.Message, state: FSMContext):
    if message.chat.type == types.ChatType.PRIVATE:
        try:
            textsing = message.text
            text_lines = textsing.strip().split('\n')
            if message.text == "/cancel":
                await message.answer(cfg.cancel_sostoyanie, parse_mode=types.ParseMode.MARKDOWN)
                await state.reset_state()
            elif message.text == cfg.cancel_button:
                user_id = message.from_user.id
                first_name = message.from_user.first_name
                username = message.from_user.username
                if (not db.check_user(user_id)):
                    db.add_user(user_id, first_name, username)
                markup_reply = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
                markup_reply.add(cfg.autoposting)
                markup_reply.add(cfg.parser)
                markup_reply.row(cfg.my_profile, cfg.support)
                if db.select_admin(user_id) > 0:
                    markup_reply.add(cfg.admin_panel_button)

                await message.answer(cfg.cancel_sostoyanie, reply_markup=markup_reply, parse_mode=types.ParseMode.MARKDOWN)
                await state.reset_state()
            else:
                if 2 <= len(message.text) <= 500:
                    if 1 <= len(text_lines) <= 20:
                        try:
                            user_id = message.from_user.id
                            first_name = message.from_user.first_name
                            username = message.from_user.username
                            if (not db.check_user(user_id)):
                                db.add_user(user_id, first_name, username)
                            markup_reply = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
                            markup_reply.add(cfg.autoposting)
                            markup_reply.add(cfg.parser)
                            markup_reply.row(cfg.my_profile, cfg.support)
                            if db.select_admin(user_id) > 0:
                                markup_reply.add(cfg.admin_panel_button)
                            data = await state.get_data()
                            number_group = data.get("number_group")
                            db.update_keywords(text_lines, number_group)
                            group_name = db.get_group_name_number(number_group)
                            await message.answer(cfg.correct_keyword_change(group_name), parse_mode=types.ParseMode.MARKDOWN, reply_markup=markup_reply)
                            await state.finish()
                        except Exception as es:
                            await state.reset_state()
                            user_id = message.from_user.id
                            first_name = message.from_user.first_name
                            username = message.from_user.username
                            if (not db.check_user(user_id)):
                                db.add_user(user_id, first_name, username)
                            markup_reply = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True,
                                                                     one_time_keyboard=False)
                            markup_reply.add(cfg.autoposting)
                            markup_reply.add(cfg.parser)
                            markup_reply.row(cfg.my_profile, cfg.support)
                            if db.select_admin(user_id) > 0:
                                markup_reply.add(cfg.admin_panel_button)
                            await message.answer(cfg.error_change_keyword_1, parse_mode=types.ParseMode.MARKDOWN, reply_markup=markup_reply)
                            print(f"[ERROR] {es}")
                    else:
                        await message.answer(cfg.error_len_keyword_create, parse_mode=types.ParseMode.MARKDOWN)
                else:
                    await message.answer(cfg.error_len_keyword, parse_mode=types.ParseMode.MARKDOWN)
        except Exception:
            await message.answer("Произошла ошибка, пожалуйста повторите ещё раз:")

@dp.message_handler(state=Create_group.create_group_1)
async def create_group_func_1(message: types.Message, state: FSMContext):
    if message.chat.type == types.ChatType.PRIVATE:
        try:
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
        except Exception:
            await message.answer("Произошла ошибка, пожалуйста повторите ещё раз:")

@dp.callback_query_handler(state=Create_group.create_group_1)
async def button_group_1(callback_query: types.CallbackQuery):
    if callback_query.data is not None:
        await callback_query.answer(cfg.error_button_create_group, show_alert=True)

@dp.message_handler(state=Create_group.create_group_2)
async def create_group_func_2(message: types.Message, state: FSMContext):
    if message.chat.type == types.ChatType.PRIVATE:
        try:
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
        except Exception:
            await message.answer("Произошла ошибка, пожалуйста повторите ещё раз:")

@dp.callback_query_handler(state=Create_group.create_group_2)
async def button_group_2(callback_query: types.CallbackQuery):
    if callback_query.data is not None:
        await callback_query.answer(cfg.error_button_create_group, show_alert=True)

@dp.message_handler(state=Create_group.create_group_3)
async def create_group_func_3(message: types.Message, state: FSMContext):
    if message.chat.type == types.ChatType.PRIVATE:
        try:
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
                    if 1 <= len(text_lines) <= 50:
                        try:
                            channels_name_1 = []
                            await message.answer(cfg.please_wait_add_channels_name)
                            for channel_name in text_line:
                                if channel_name[13] == "+":
                                    response = requests.get(channel_name)
                                    html_content = response.text
                                    soup = BeautifulSoup(html_content, 'html.parser')
                                    title_div = soup.find('div', {'class': 'tgme_page_title'})
                                    if title_div:
                                        group_name = title_div.get_text(strip=True)
                                        channels_name_1.append(group_name)
                                    else:
                                        await message.answer(cfg.error_channel_name_add)
                                        break
                                elif channel_name[0] == "@":
                                    response = requests.get(f"https://t.me/{channel_name[1:]}")
                                    html_content = response.text
                                    soup = BeautifulSoup(html_content, 'html.parser')
                                    title_div = soup.find('div', {'class': 'tgme_page_title'})
                                    if title_div:
                                        group_name = title_div.get_text(strip=True)
                                        channels_name_1.append(group_name)
                                    else:
                                        await message.answer(cfg.error_channel_name_add)
                                        break
                                else:
                                    response = requests.get(f"https://t.me/{channel_name}")
                                    html_content = response.text
                                    soup = BeautifulSoup(html_content, 'html.parser')
                                    title_div = soup.find('div', {'class': 'tgme_page_title'})
                                    if title_div:
                                        group_name = title_div.get_text(strip=True)
                                        channels_name_1.append(group_name)
                                    else:
                                        await message.answer(cfg.error_channel_name_add)
                                        break
                            if len(channels_name_1) == len(text_line):
                                channels_name_2 = list(dict.fromkeys([element + ' ⚠' for element in channels_name_1]))
                                check_number_group = db.check_numbers_group()
                                new_number_group = check_number_group + 1
                                data = await state.get_data()
                                cashe_group_name = data.get('group_name')
                                cashe_keyword = data.get('text_lines')
                                db.add_channels(user_id, new_number_group, cashe_keyword, text_lines, cashe_group_name, channels_name_2)
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
        except Exception:
            await message.answer("Произошла ошибка, пожалуйста повторите ещё раз:")

@dp.callback_query_handler(state=Create_group.create_group_3)
async def button_group_2(callback_query: types.CallbackQuery):
    if callback_query.data is not None:
        await callback_query.answer(cfg.error_button_create_group, show_alert=True)

@dp.message_handler(state=Add_chat_ids.panel_adm)
async def panel_adm(message: types.Message, state: FSMContext):
    try:
        if message.text == cfg.back_button:
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
    except Exception:
        await message.answer("Произошла ошибка, пожалуйста повторите ещё раз:")

@dp.message_handler(state=Add_chat_ids.add_ids_1)
async def add_chat_ids_num_1(message: types.Message, state: FSMContext):
    try:
        if message.text == cfg.back_button:
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
    except Exception:
        await message.answer("Произошла ошибка, пожалуйста повторите ещё раз:")

@dp.message_handler(state=Add_chat_ids.add_ids_2)
async def add_chat_ids_num_2(message: types.Message, state: FSMContext):
    try:
        if message.text == cfg.back_button:
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
            all_channels = db.select_channels_with_number(number_group)
            for channel_name in all_channels:
                if channel_name[-1] == "✅":
                    index_channel = all_channels.index(channel_name)
                    all_channels_name = db.select_channels_name_with_number(number_group)
                    group_name = all_channels_name[index_channel]
                    new_callback_name = group_name[:-1] + "✅"
                    new_channels_name = [new_callback_name if item == group_name else item for item in all_channels_name]
                    db.update_all_channels_name(number_group, new_channels_name)
            new_list_all = []
            old_chat_list = db.select_chat_ids(number_group) or []
            channels_pars = db.select_channels_number_group(number_group)
            channels_link_parser = [item for item in channels_pars if len(item) >= 13 and item[13] == '+']
            for ownn_lst in new_lst:
                index = int(ownn_lst[0])
                link_id_lst = [ownn_lst, channels_link_parser[index - 1][:-2]]
                new_list_all.append(link_id_lst)
            new_lstss = old_chat_list + new_list_all
            db.add_chat_ids(int(number_group), new_lstss)
            await message.answer(cfg.correct_add_chat_ids, reply_markup=markup_reply, parse_mode=types.ParseMode.MARKDOWN)
            await Add_chat_ids.panel_adm.set()
    except Exception:
        await message.answer("Произошла ошибка, попробуйте ещё раз:")

@dp.message_handler(state=Create_account_autoposting.create_autoposting_1)
async def process_phone(message: types.Message, state: FSMContext):
    try:
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
                    await message.reply("Теперь отправьте код, который вы получили от Telegram.\n\nВажно! Пожалуйста, НЕ присылай мне код как есть (иначе он сразу перестанет действовать). Пришли мне его, разделив цифры пробелами. Например, 123 45 или 1 2345, где 12345 - это сам код, который ты получил от Телеграма.")
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
                    int(code)
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
                except ValueError:
                    await message.answer("Произошла ошибка! Код должен состоять исключительно из цифр, пожалуйста повторите попытку:")
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
    except Exception:
        await message.answer("Произошла ошибка, пожалуйста повторите ещё раз:")

@dp.message_handler(state=Create_account_autoposting.create_autoposting_2)
async def group_name_autoposting(message: types.Message, state: FSMContext):
    if message.chat.type == types.ChatType.PRIVATE:
        try:
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
                    user_id = message.from_user.id
                    first_name = message.from_user.first_name
                    username = message.from_user.username
                    if (not db.check_user(user_id)):
                        db.add_user(user_id, first_name, username)
                    markup_reply = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
                    markup_reply.add(cfg.autoposting)
                    markup_reply.add(cfg.parser)
                    markup_reply.row(cfg.my_profile, cfg.support)
                    data = await state.get_data()
                    phone = data.get('phone')
                    string_session = data.get('string_session')
                    group_name = message.text
                    check_number_group = db.check_numbers_account_autoposting()
                    new_number_group = check_number_group + 1
                    db.add_autoposting_account(user_id, new_number_group, phone, string_session, group_name)
                    await message.answer(cfg.create_account_right, reply_markup=markup_reply)
                    await state.finish()
                else:
                    await message.answer("Минимальная длина названия аккаунта, должна быть 3, максимальная 15, попробуйте ещё раз:")
        except Exception:
            await message.answer("Произошла ошибка, пожалуйста повторите ещё раз:")


@dp.message_handler()
async def other(message: types.Message):
    if message.chat.type == types.ChatType.PRIVATE:
        try:
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
            else:
                await message.answer(cfg.unknown_command_text)
        except Exception:
            await message.answer("Произошла ошибка, пожалуйста повторите ещё раз:")


async def on_startup(_):
    asyncio.create_task(search_and_forward())
    asyncio.create_task(search_and_forward_close_group())
    asyncio.create_task(autoposting_forward())

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)