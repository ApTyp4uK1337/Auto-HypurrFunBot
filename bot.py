import asyncio
from telethon import TelegramClient, events
import re
from config import load_config

# Загружаем конфигурацию
config = load_config()

# Извлекаем параметры из конфигурации
API_ID = config["API_ID"]
API_HASH = config["API_HASH"]
SESSION_NAME = config["SESSION_NAME"]
CHANNEL = config["CHANNEL"]
BOT_USERNAME = config["BOT_USERNAME"]

# Создаем клиента
client = TelegramClient(f"sessions/{SESSION_NAME}", API_ID, API_HASH)

# Регулярное выражение для поиска ссылки с параметром после ?start=
link_pattern = r'http://t.me/HypurrFunBot\?start=([a-zA-Z0-9_]+)'

# Регулярное выражение для извлечения информации о покупке из сообщения
purchase_pattern = r"Bought (\d+\.?\d*) (\w+) at an average price of (\d+\.\d+) for \$(\d+\.\d+)"
value_pattern = r"Value:\s+`([0-9]+\.[0-9]+)`"


async def handle_bot_reply(user_bot, bot_username, start_data):
    try:
        print(f"Обрабатываем ответ от бота {bot_username} с данными: {start_data}")
        
        # Отправляем команду /start
        await user_bot.send_message(bot_username, f"/start {start_data}")
        print(f"Команда /start отправлена с данными: {start_data}")
        
        await asyncio.sleep(1)

        # Получаем следующее сообщение от бота (которое должно содержать кнопки)
        async for bot_reply in user_bot.iter_messages(bot_username, limit=1):
            print(f"Ответ от бота: {bot_reply.text}")

            # Проверяем, что reply_markup существует и содержит inline-кнопки
            if bot_reply.reply_markup:
                print(f"reply_markup найден: {bot_reply.reply_markup}")

                # Сохраняем ID сообщения с кнопками
                message_id = bot_reply.id

                # Нажимаем первую кнопку (например, Buy $20)
                first_button = bot_reply.reply_markup.rows[0].buttons[0]  # Первая кнопка
                print(f"Нажата первая кнопка: {first_button.text}")
                
                # Нажатие кнопки по индексу
                await bot_reply.click(0)
                
                await asyncio.sleep(1)

                # Ожидаем, что придет сообщение с информацией о покупке
                async for purchase_reply in user_bot.iter_messages(bot_username, limit=1):
                    if purchase_match := re.search(purchase_pattern, purchase_reply.text):
                        print(f"Сообщение о покупке получено: {purchase_reply.text}")
                        
                        # Извлекаем данные из сообщения о покупке
                        amount_bought = purchase_match.group(1)
                        coin = purchase_match.group(2)
                        price = purchase_match.group(3)
                        total_cost = float(purchase_match.group(4))
                        print(f"Куплено: {amount_bought} {coin} по цене {price} за {total_cost}$")
                        
                        # Нажимаем кнопку Refresh и проверяем Value
                        refresh_button = bot_reply.reply_markup.rows[2].buttons[0]  # Кнопка Refresh
                        sell_button = bot_reply.reply_markup.rows[1].buttons[1]  # Кнопка Sell
                        
                        while True:
                            # Нажимаем кнопку Refresh
                            print(f"Нажатие кнопки {refresh_button.text}")
                            await bot_reply.click(0)  # Индекс кнопки Refresh

                            await asyncio.sleep(1)  # Ждем обновления текста

                            # Получаем обновленный текст сообщения по ID
                            updated_reply = await user_bot.get_messages(bot_username, ids=message_id)

                            # Проверяем текст текущего сообщения на наличие Value
                            if value_match := re.search(value_pattern, updated_reply.text):
                                current_value = float(value_match.group(1))
                                print(f"Текущее значение Value: {current_value}")

                                # Если Value превышает 30% от суммы покупки
                                if current_value >= total_cost * 1.3:  # 30% от суммы покупки
                                    print(f"Value превышает 30% от суммы покупки! Нажимаем кнопку {sell_button.text}")
                                    await updated_reply.click(4)  # Индекс кнопки Sell (проверьте правильность индекса)
                                    
                                    return
                            else:
                                print("Значение Value не найдено.")
                                    
                            await asyncio.sleep(2)
                    else:
                        print("Сообщение о покупке не найдено.")
            else:
                print("Кнопки не найдены в ответе бота.")
    except Exception as e:
        print(f"Ошибка при обработке сообщения от бота: {e}")


async def monitor_channel(message):
    try:
        print(f"Обрабатываем сообщение: {message.text}")
        # Проверяем на наличие ссылки
        match = re.search(link_pattern, message.text)
        if match:
            start_data = match.group(1)
            print(f"Найдена ссылка, начинаем взаимодействие с ботом {BOT_USERNAME}, start_data: {start_data}")
            # Создаем асинхронную задачу для обработки сообщения
            asyncio.create_task(handle_bot_reply(client, BOT_USERNAME, start_data))
        else:
            print("Ссылка не найдена в сообщении")
    except Exception as e:
        print(f"Ошибка при мониторинге канала: {e}")


@client.on(events.NewMessage(chats=CHANNEL))
async def on_message(event):
    message = event.message
    print(f"Новое сообщение от канала {CHANNEL}: {message.text}")
    # Создаем асинхронную задачу для обработки нового сообщения
    asyncio.create_task(monitor_channel(message))


# Запускаем клиента
print(f"User bot запущен и слушает канал {CHANNEL}...")
client.start()
client.run_until_disconnected()
