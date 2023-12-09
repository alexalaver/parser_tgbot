import re

a = "Здравствуйте, вот допустим ваш '5', что вы хотите сделать"

matches = re.findall(r"'([^']*)'", a)

print(matches[0])