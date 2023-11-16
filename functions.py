from aiogram.utils.markdown import link

def nick_with_link(text, blink):
    return link(f"{text}", f"tg://user?id={blink}")

def get_category(a):
    if 1 <= a <= 10:
        return 1
    elif 11 <= a <= 20:
        return 2
    elif 21 <= a <= 30:
        return 3
    elif 31 <= a <= 40:
        return 4
    elif 41 <= a <= 50:
        return 5