# import requests
# from bs4 import BeautifulSoup
#
# url = 'https://t.me/@asdasdas'
#
# response = requests.get(url)
# html_content = response.text
#
# soup = BeautifulSoup(html_content, 'html.parser')
#
# title_div = soup.find('div', {'class': 'tgme_page_title'})
# if title_div:
#     group_name = title_div.get_text(strip=True)
#     print("Название группы:", group_name)
# else:
#     print("Название группы не найдено.")

# from datetime import datetime
# import pytz
#
# a = "10:30"
# hours, minutes = map(int, a.split(':'))
#
# # Получаем текущую дату
# current_date = datetime.now()
#
# # Объединяем текущую дату с временем из `a`
# combined_datetime = current_date.replace(hour=hours, minute=minutes, second=0, microsecond=0)
#
# # Форматируем результат в строку
# formatted_datetime = combined_datetime.strftime("%Y-%m-%d %H:%M:%S")
#
# print(formatted_datetime)

# a = [
#     ["https://t.me/testonepublic ✅", "2023-12-16 12:30:00"],
#     ["https://t.me/testtwopublic ✅", "2023-12-16 12:30:00"],
#     ["https://t.me/testthreepublic ✅", "2023-12-16 12:30:00"],
#     ["https://t.me/+kaLhqGj2EHg3NjFi ✅", "2023-12-16 12:30:00", "2023-12-16 14:30:00"]
# ]
# b = "https://t.me/+kaLhqGj2EHg3NjFi ✅"
#
# # Выбор подсписка, где первый элемент равен 'b'
# selected_sublist = [sublist for sublist in a if sublist[0] == b]
#
# # Поскольку нужен только один элемент, мы берем первый подходящий подсписок
# result = selected_sublist[0] if selected_sublist else []
# times = [datetime_str.split()[1][:5] for datetime_str in result[1:]]
#
# print(result)

chat_idn = ["https://t.me/doubletop_otc ✅", "https://t.me/+kaLhqGj2EHg3NjFi ✅", "@testonepublic ✅", "https://t.me/+kaLasdasd ✅"]
chat_name = ["2TOP OTC ✅", "TESTPRIVATE5 ✅", "testonepublic ✅", "TESTING ✅"]

# Фильтруем открытые чаты, сохраняя их индексы
chat_ids_with_indices = [(index, item) for index, item in enumerate(chat_idn) if item.endswith('✅') and not ('https://t.me/+' in item)]

# Получаем индексы отфильтрованных открытых чатов
chat_indices = [index for index, _ in chat_ids_with_indices]

# Используем эти индексы для выбора соответствующих названий из chat_name
chat_names = [chat_name[index] for index in chat_indices]

print(chat_names)