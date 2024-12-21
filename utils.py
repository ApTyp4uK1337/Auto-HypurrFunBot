import re

# Регулярные выражения
bot_link_pattern = re.compile(r"http://t\.me/HypurrFunBot\?start=([a-zA-Z0-9_]+)")
amount_pattern = re.compile(r"Bought\s+[\d.]+\s+[A-Za-z]+\s+at\s+an\s+average\s+price\s+of\s+[\d.]+\s+for\s+\$(\d+\.\d+)")

# Функция для извлечения ссылки
def extract_bot_link(text):
    return bot_link_pattern.search(text)

# Функция для извлечения суммы (amount)
def extract_amount(text):
    amount_match = amount_pattern.search(text)
    return float(amount_match.group(1)) if amount_match else None
