from aiogram.utils.markdown import link

def nick_with_link(text, blink):
    return link(f"{text}", f"tg://user?id={blink}")
