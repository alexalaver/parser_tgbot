from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
import config as cfg


def profile_buttons():
    markup = InlineKeyboardMarkup(row_width=1)
    btn_1 = InlineKeyboardButton(cfg.up_balance, callback_data='up_balance')
    markup.add(btn_1)
    return markup


def support_buttons(admin_id):
    markup = InlineKeyboardMarkup(row_width=1)
    btn_1 = InlineKeyboardButton(cfg.support, callback_data='support', url=f"tg://user?id={admin_id[1]}")
    markup.add(btn_1)
    return markup

def parsers_button_menu(group_names):
    markup = InlineKeyboardMarkup(row_width=1)
    for group_name in group_names:
        button = InlineKeyboardButton(text=group_name, callback_data=f"{group_name}parsers")
        markup.add(button)

    btn_1 = InlineKeyboardButton(cfg.groups_add_button, callback_data='groups_add_button_parser')
    markup.add(btn_1)
    return markup

def autoposting_button_menu(group_names):
    markup = InlineKeyboardMarkup(row_width=1)
    for group_name in group_names:
        button = InlineKeyboardButton(text=group_name, callback_data=f"{group_name}autoposting_account")
        markup.add(button)
    btn_1 = InlineKeyboardButton(cfg.add_account_button, callback_data="add_account_autoposting")
    markup.add(btn_1)
    return markup

def menu_buttons(admin):
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
    markup.add(cfg.autoposting)
    markup.add(cfg.parser)
    markup.row(cfg.my_profile, cfg.support)
    if admin > 0:
        markup.add(cfg.admin_panel_button)

    return markup

def cancel_button():
    markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    markup.add(cfg.cancel_button)
    return markup

def enter_group_button(paired_channels, page_here_parser, channels_page_parser, channels_count_parser, check_tarife):
    markup = InlineKeyboardMarkup(row_width=2)
    for channel_name, channel in paired_channels:
        button = InlineKeyboardButton(text=channel_name, callback_data=channel)
        markup.row(button)
    buttons_count = InlineKeyboardButton(text=f"Страница {page_here_parser}/{channels_page_parser} 📄", callback_data="page_parser")
    markup.add(buttons_count)
    if channels_count_parser > 10:
        buttons_next = InlineKeyboardButton(text=cfg.next_page, callback_data="next_page_parser")
        buttons_old = InlineKeyboardButton(text=cfg.old_page, callback_data="old_page_parser")
        markup.row(buttons_old, buttons_next)
    if check_tarife is None:
        pay_money_buttons = InlineKeyboardButton(text=cfg.pay_money_channels, callback_data='pay_money_channels_parser')
        markup.add(pay_money_buttons)
    change_keywords = InlineKeyboardButton(text=cfg.keyword_parser_buttons, callback_data='keyword_parser')
    back_channels = InlineKeyboardButton(text=cfg.back_channels, callback_data='back_channels_parser')
    markup.add(change_keywords)
    markup.add(back_channels)
    return markup

def enter_account_button(group_names):
    markup = InlineKeyboardMarkup(row_width=1)
    for group_name in group_names:
        button = InlineKeyboardButton(text=group_name, callback_data=f"{group_name}autoposting_post")
        markup.add(button)
    btn_1 = InlineKeyboardButton(cfg.add_post_button, callback_data="add_post_autoposting")
    btn_2 = InlineKeyboardButton(cfg.back_button, callback_data="back_autoposting_account")
    markup.add(btn_1, btn_2)
    return markup

def enter_account_post_button(paired_channels, page_here_autoposting, channels_page_autoposting, channels_count_autoposting, check_tarife):
    markup = InlineKeyboardMarkup(row_width=1)
    for channel_name, channel in paired_channels:
        buttons = InlineKeyboardButton(text=channel_name, callback_data=channel)
        markup.row(buttons)
    buttons_count = InlineKeyboardButton(text=f"Страница {page_here_autoposting}/{channels_page_autoposting} 📄", callback_data="page_autoposting")
    markup.add(buttons_count)
    if channels_count_autoposting > 10:
        buttons_next = InlineKeyboardButton(text=cfg.next_page, callback_data="next_page_autoposting")
        buttons_old = InlineKeyboardButton(text=cfg.old_page, callback_data="old_page_autoposting")
        markup.row(buttons_old, buttons_next)
    if check_tarife is None:
        pay_money_buttons = InlineKeyboardButton(text=cfg.pay_money_channels, callback_data='pay_money_channels_autoposting')
        markup.add(pay_money_buttons)
    back_channels = InlineKeyboardButton(text=cfg.back_channels, callback_data='back_channels_autoposting')
    delete_post_button = InlineKeyboardButton(text=cfg.delete_post_button,callback_data="delete_post_autoposting")
    markup.add(delete_post_button, back_channels)
    return markup

def confirm_back_oplata_button():
    markup = InlineKeyboardMarkup(row_width=1)
    btn_1 = InlineKeyboardButton(cfg.confirm_oplata, callback_data='confirm_oplata_parser')
    btn_2 = InlineKeyboardButton(cfg.back_button, callback_data='back_oplata_parser')
    markup.add(btn_1, btn_2)
    return markup

def keyword_button():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(text=cfg.change_keyword_button, callback_data="change_keyword_parser"),
        InlineKeyboardButton(text=cfg.back_button, callback_data="back_from_keyword_parser")
    )
    return markup

def click_chat_in_autoposting_post_button(times, channel_name):
    markup = InlineKeyboardMarkup(row_width=1)
    for time in times:
        button = InlineKeyboardButton(text=time, callback_data=time)
        markup.add(button)
    if channel_name[-1] == "✅":
        markup.add(InlineKeyboardButton(text=cfg.off_chat_button, callback_data="off_chat_autoposting"))
    elif channel_name[-1] == "❌":
        markup.add(InlineKeyboardButton(text=cfg.on_chat_button, callback_data="on_chat_autoposting"))
    markup.add(
        InlineKeyboardButton(text=cfg.add_time_button, callback_data="add_time_autoposting_chat"),
        InlineKeyboardButton(text=cfg.back_button, callback_data="back_settings_chat_time_autoposting")
    )
    return markup

def click_time_in_post_group_button():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(cfg.change_time_chat_button, callback_data="change_time_chat_button_autoposting"),
        InlineKeyboardButton(cfg.back_button, callback_data="back_change_time_chat_button_autoposting"),
        InlineKeyboardButton(cfg.delete_time_chat_button, callback_data="delete_time_chat_button_autoposting")
    )
    return markup

def button_yes_no_delete_time_group_post():
    markup = InlineKeyboardMarkup(row_width=1)
    btn_yes = InlineKeyboardButton("Да", callback_data='yes_delete_time_autoposting')
    btn_no = InlineKeyboardButton("Нет", callback_data='no_delete_time_autoposting')
    markup.add(btn_yes, btn_no)
    return markup

def button_yes_no_delete_post_group():
    markup = InlineKeyboardMarkup(row_width=1)
    btn_yes = InlineKeyboardButton("Да", callback_data='yes_delete_autoposting')
    btn_no = InlineKeyboardButton("Нет", callback_data='no_delete_autoposting')
    markup.add(btn_yes, btn_no)
    return markup

def confirm_back_oplata_button_autoposting():
    markup = InlineKeyboardMarkup(row_width=1)
    btn_1 = InlineKeyboardButton(cfg.confirm_oplata, callback_data='confirm_oplata_autoposting')
    btn_2 = InlineKeyboardButton(cfg.back_button, callback_data='back_oplata_autoposting')
    markup.add(btn_1, btn_2)
    return markup

def menu_after_pay_autoposting_button():
    markup = InlineKeyboardMarkup(row_width=1)
    btn_1 = InlineKeyboardButton(cfg.menu_button, callback_data='menu_after_pay_autoposting')
    markup.add(btn_1)
    return markup

def buttons_in_panel_adm():
    markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    markup.add(cfg.add_chat_id_button, cfg.add_proxy_button, cfg.back_button)
    return markup

def button_black_list(username, user_id, first_name):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(text=cfg.black_list_add_username_button, callback_data=f"black_list_add_username_button:{username}:{user_id}:{first_name}"),
        InlineKeyboardButton(text=cfg.black_list_add_post_button, callback_data=f"black_list_add_post_button:{username}:{user_id}:{first_name}"),
        InlineKeyboardButton(text=cfg.black_list_button, callback_data=f"black_list_button:{username}:{user_id}:{first_name}")
    )
    return markup

def confirm_black_list_button_user(info):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(text=cfg.confirm_button, callback_data=f"confirm_black_list_user:{info[1]}:{info[2]}:{info[3]}"),
        InlineKeyboardButton(text=cfg.back_channels, callback_data="back_from_confirm_black_list_user")
    )
    return markup

def confirm_black_list_button_post(info):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(text=cfg.confirm_button, callback_data=f"confirm_black_list_post:{info[1]}:{info[2]}:{info[3]}"),
        InlineKeyboardButton(text=cfg.back_channels, callback_data="back_from_confirm_black_list_user")
    )
    return markup

def black_list_button_all(username, user_id, first_name):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(text=cfg.users_black_list_button, callback_data=f"users_black_list_button:{username}:{user_id}:{first_name}"),
        InlineKeyboardButton(text=cfg.posts_black_list_button, callback_data=f"posts_black_list_button:{username}:{user_id}:{first_name}"),
        InlineKeyboardButton(text=cfg.back_button, callback_data=f"back_from_black_list_all:{username}:{user_id}:{first_name}")
    )
    return markup

def black_list_users_button_all(users_black_list_all, username, user_id, first_name):
    markup = InlineKeyboardMarkup(row_width=1)
    for us_black in users_black_list_all:
        button = InlineKeyboardButton(text=us_black[1], callback_data=f"select_user_black_list:{us_black[0]}:{username}:{user_id}:{first_name}")
        markup.add(button)
    btn_1 = InlineKeyboardButton(cfg.back_button, callback_data=f"back_from_black_list_users_all:{username}:{user_id}:{first_name}")
    markup.add(btn_1)
    return markup

def black_list_select_user_button(user_id_black, username, user_id, first_name):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(text=cfg.delete_user_from_black_list_button, callback_data=f"delete_user_from_black_list:{user_id_black}"),
        InlineKeyboardButton(text=cfg.back_button, callback_data=f"back_from_delete_user:{username}:{user_id}:{first_name}")
    )
    return markup