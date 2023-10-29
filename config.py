TOKEN = "6597828235:AAH60BBRislfPCqwBeGsiYMBEjXuBrHujZ0"
def profile(profile_id, balance, tariffe):
    return f"*Ваш идентификатор: *{profile_id}\n*Текущий баланс: *{balance}\n*Ваш тариф: *{tariffe}"

up_balance = "Пополнение баланса"
tariff_selection = "Выбор тарифа"

autoposting = "Автопостинг"
parser = "Парсер"
my_profile = "Мой профиль"
support = "Саппорт"

tariff_list = "*Ниже предоставлены основные тарифы.\nМаксимальное количество чатов для парсинга - 50,\nесли вам необходимо больше - свяжитесь с саппортом*"
start_tariff_button = "Стартовый 10 чатов - 15$"
standart_tariff_button = "Стандарт 25 чатов - 39$"
premium_tariff_button = "Премиум 50 чатов - 69$"
back_button = "Назад"
back_text = "Вы вернулись назад."
tariff_list_text = "Вы зашли в список тарифов."

error_not_found_user = "Такого пользователя не существует!"

def right_add_admin(polz):
    return f"Вы успешно добавили {polz}!"

error_command = "Вы ввели команду в неправильно формате.\nПравильный формат - /add_admin _id_"

error_adm_dostup = "У вас не достаточно прав для команды."

def balance_user_text(polz, balance):
    return f"У данного {polz}, {balance}"

balance_command_error = "Вы ввели команду в неправильном формате.\nПравильный формат - /balance _id_"
addbalance_command_error = "Вы ввели команду в неправильном формате.\nПравильный формат - /addbalance _id_ _сумма_"
rembalance_command_error = "Вы ввели команду в неправильном формате.\nПравильный формат - /rembalance _id_ _сумма_"

def addbalance_right_admin(polz, balance):
    return f"Вы успешно прибавили {balance}$, {polz}."

def addbalance_right_polz(balance):
    return f"Администратор, прибавил к вашему балансу {balance}$"

def rembalance_right_admin(polz, balance):
    return f"Вы успешно сняли {balance}$, {polz}."

def rembalance_right_polz(balance):
    return f"Администратор, снял с вашего баланса {balance}$"

support_correct_text = "Вы зашли в меню службу поддержки"

chats_button = "Чаты"
word_poisk_button = "Слова для поиска"

parser_text = "В данном разделе вы можете настроить поиск ключевых слов по нужным чатам.\nПеред использованием парсинга - не забудьте выбрать подходящий тариф в профиле"

account_button = "Аккаунты"
posts_button = "Посты"
autoposting_text = "В этом разделе вы можете настроить всё, что связанно с автопостингом"

take_adm = "Вас повысили до 1 уровня администратора."