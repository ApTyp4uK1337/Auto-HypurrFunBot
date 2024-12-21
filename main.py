import re
import asyncio
from pyrogram import Client, filters
from config_manager import load_config  # Импортируем функцию для загрузки конфигурации
from session_manager import create_client  # Импортируем функцию для создания клиента

# Загружаем конфигурацию
config = load_config()

# Извлекаем параметры из конфигурации
API_ID = config["API_ID"]
API_HASH = config["API_HASH"]
SESSION_NAME = config["SESSION_NAME"]
CHANNEL = config["CHANNEL"]

# Создаем клиента с помощью функции из session_manager.py
app = create_client(SESSION_NAME, API_ID, API_HASH)

# Регулярное выражение для поиска ссылок вида http://t.me/SomeBot?start=some_data
bot_link_pattern = re.compile(r"http://t\.me/([a-zA-Z0-9_]+)\?start=([a-zA-Z0-9_]+)")

# Регулярное выражение для извлечения значения Value
value_pattern = re.compile(r"Value:\s+([0-9.]+)")

@app.on_message(filters.chat(CHANNEL) & filters.text)
async def monitor_channel(client, message):
    # Проверяем текст на наличие ссылки
    match = bot_link_pattern.search(message.text)
    if match:
        bot_username = match.group(1)  # Имя бота (например, HypurrFunBot)
        start_data = match.group(2)  # Параметр start (например, launch_8207)
        print(f"Найдена ссылка: @{bot_username}, start: {start_data}")

        # Переходим в бота и отправляем /start с параметром
        response = await client.send_message(bot_username, f"/start {start_data}")
        print("Отправлена команда /start")

        # Ожидаем последнее сообщение от бота
        async for bot_reply in app.get_chat_history(bot_username, limit=1):
            print("Ответ от бота:", bot_reply.text)

            # Проверяем наличие inline-кнопок
            if bot_reply.reply_markup and bot_reply.reply_markup.inline_keyboard:
                # Нажимаем первую кнопку в первом ряду
                first_row_button = bot_reply.reply_markup.inline_keyboard[0][0]
                await bot_reply.click(first_row_button)
                print("Нажата первая кнопка в первом ряду:", first_row_button.text)

                # Переходим к циклу нажатия в третьем ряду с интервалом в 3 секунды
                while True:
                    # Нажимаем кнопку с интервалом
                    await bot_reply.click(first_row_button)
                    print("Нажата кнопка в третьем ряду:", first_row_button.text)
                    await asyncio.sleep(3)

                    # Проверяем обновленное сообщение
                    async for updated_reply in app.get_chat_history(bot_username, limit=1):
                        if updated_reply.text:
                            print("Обновленное сообщение:", updated_reply.text)
                            # Извлекаем значение Value
                            value_match = value_pattern.search(updated_reply.text)
                            if value_match:
                                current_value = float(value_match.group(1))
                                print(f"Текущее значение Value: {current_value}")

                                # Если значение превышает 130.000000, нажимаем кнопку во втором ряду
                                if current_value > 130.000000:
                                    second_row_button = updated_reply.reply_markup.inline_keyboard[1][1]
                                    await updated_reply.click(second_row_button)
                                    print("Нажата кнопка во втором ряду:", second_row_button.text)
                                    return

# Запускаем user bot
print("User bot запущен и слушает канал " + CHANNEL + "...")
app.run()
