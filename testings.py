import requests
from bs4 import BeautifulSoup

url = 'https://t.me/@asdasdas'

response = requests.get(url)
html_content = response.text

soup = BeautifulSoup(html_content, 'html.parser')

title_div = soup.find('div', {'class': 'tgme_page_title'})
if title_div:
    group_name = title_div.get_text(strip=True)
    print("Название группы:", group_name)
else:
    print("Название группы не найдено.")

a = "Hello"
print(a[-1])


a_text = ["Symon", "Dindo", "Lolo"]
b_text = "Lolo"
print(a_text.index(b_text))
