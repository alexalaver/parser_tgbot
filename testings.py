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
a = ['-1001510977035 ⚠️', '-1001736743858 ⚠️', '-1001213408970 ⚠️', '-1001878678108 ⚠️', '-1001517774064 ⚠️', '-1001705213339 ⚠️', '-1001279574075 ⚠️', '-1001683121035 ⚠️', '-1001696310170 ⚠️', '-1001650231363 ⚠️', '-1001851304640 ⚠️', '-1001514722834 ⚠️', '-1001677058295 ⚠️', '-1001877669709 ⚠️', '-1001674655522 ⚠️', '-1001328817518 ⚠️', '-1001605199078 ⚠️', '-1001597998355 ⚠️', '-1001948194729 ⚠️', '-1001580175916 ⚠️', '-1001923149774 ⚠️', '-1001752221510 ⚠️', '-1001517407287 ⚠️', '-1001779341796 ⚠️', '-1001896940199 ⚠️', '-1001635034914 ⚠️', '-1001621632301 ⚠️', '-1001801359698 ⚠️', '-1001602280233 ⚠️', '-1001686686186 ⚠️', '-1001461827575 ⚠️', '-1001249220364 ⚠️', '-1001549236483 ⚠️', '-4039465465 ⚠️', '-4078334833 ⚠️', '-4066982254 ⚠️', '-4004407892 ⚠️', '-4069402198 ⚠️', '-4095027897 ⚠️', '-4012396350 ⚠️', '-1001900518404 ⚠️', '-1001467130623 ⚠️', '-1001207474533 ⚠️', '-1001993377284 ⚠️', 'https://t.me/cardeurope ⚠️']

print(len(a))