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
from datetime import datetime

# Given data
a = [
    ["https://t.me/testonepublic ✅", "2023-12-17 12:30:00"],
    ["https://t.me/testtwopublic ❌", "2023-12-17 12:30:00", "2023-12-16 22:35:00"],
    ["https://t.me/testthreepublic ❌", "2023-12-17 12:30:00", "2023-12-17 17:25:00", "2023-12-17 21:30:00"],
    ["https://t.me/+kaLhqGj2EHg3NjFi ❌", "2023-12-17 12:30:00"]
]

b = "12:30"
c = "14:40"

# Function to check and replace the time
def check_and_replace_times(data, time_to_check, replacement_time):
    # Format for time comparison
    time_format = "%H:%M"

    # Iterate through each sublist in the data
    for sublist in data:
        # Iterate through each item in the sublist starting from the first time element
        for i in range(1, len(sublist)):
            # Compare time part only
            if datetime.strptime(sublist[i], "%Y-%m-%d %H:%M:%S").strftime(time_format) == time_to_check:
                # Replace date keeping the same date but changing the time
                sublist[i] = sublist[i].replace(time_to_check, replacement_time)

    return data

# Apply the function to the data
updated_a = check_and_replace_times(a, b, c)
print(updated_a)