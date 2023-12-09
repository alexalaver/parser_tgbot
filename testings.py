import re

a = "Здравствуйте, вот допустим ваш 'post 1', что вы хотите сделать"

matches = re.findall(r"'([^']*)'", a)

print(matches[0])