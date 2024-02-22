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