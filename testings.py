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
a = ["PLATINUM GANG 🪙 ❌","Живи футболом | Наш футбольный чат ✅","𝗕𝗜𝗚𝗙𝗔𝗧𝗖𝗛𝗔𝗧™️💰 ❌","𝗩𝗘𝗥𝗜𝗙 𝗖𝗛𝗔𝗧 ❌","Asmodeus Chat🩸 ❌","Shadow Chat ❌","Ghostly ❌","Action Chat 💎 ❌","Marlboro | Услуги По USA ❌","XTERNAL GROUP ❌","ForumGram ❌","♠️ 𝐂𝐋 𝐏𝐔𝐁𝐋𝐈𝐂 𝐂𝐇𝐀𝐓 ♠️ ❌","𝗩𝗘𝗥𝗜𝗙 𝗖𝗛𝗔𝗧 ❌","El Dorado Chat ❌","Ебучий ADS Чат 3.0 ❌","stuff 4 all ❌","🎄Brotherhood. ❌","Фруктовая Лавка 🏬 ❌","SPAIN FAMILY CHAT ❌","CASH APP CHAT 💰 ❌","Фруктовая Лавка 🏬 ❌","BRAZZERS Corporation 🔞 ✅","𝗕𝗜𝗚𝗙𝗔𝗧𝗖𝗛𝗔𝗧™️💰 ❌","Atomic Supply // Chat // Benji Corp ✅","𝗩𝗘𝗥𝗜𝗙 𝗖𝗛𝗔𝗧 ❌","VSE O DARKNET ✅","CCC ☠️☠️☠️ ✅","SPECTRUM CHAT ✅","Port Royal ✅","Belosnejka CHAT ✅","Ｐ𝖆 y D 𝖆 y сhat ✅","GYM [18+См] ✅","Carding Family ✅","Black Wallet VIP/ CHAT ✅","AgentCorporation Chat ✅","Safe 🧦 Socks ✅","TextVerified REAL USA SMS ✅","TESTPRIVATE4 ✅","TESTPRVIATE1 ✅","test1PRIVATE ✅","TESTPRIVATE6 ✅","test9private ✅","test10private ✅","test5PRIVATE ✅","USA2CIS Chat ✅","Bank Of America ✅","Фруктовая Лавка 🏬 ❌","🎲Elite🎭_GG ✅","💲AID | CHAT💲\\ ✅","EuroCard • Worldwide 💳 ✅"]

print(len(a))