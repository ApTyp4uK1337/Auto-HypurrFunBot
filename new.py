import os
import sys
import asyncio
import re
import logging
import shutil
import json
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logging.getLogger('telethon.client.updates').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Загрузка конфигурации
def load_config():
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    global API_ID, API_HASH, BOT_USERNAME, MESSAGE_AWAIT, REFRESH_AWAIT
    global BUY_BUTTON, REFRESH_BUTTON, SELL_BUTTON
    global SESSION_NAME, SESSION_FOLDER, SESSION_FILE, USER_CONFIG_FILE
    global CHANNELS, ALERTS_CHANNEL, MIN_REPUTATION, MIN_DEV_LOCK, BAN_WORDS
    global MAX_PROFIT_PERCENT, MAX_LOSS_PERCENT

    API_ID = config["API_ID"]
    API_HASH = config["API_HASH"]
    BOT_USERNAME = config["BOT_USERNAME"]
    MESSAGE_AWAIT = config["MESSAGE_AWAIT"]
    REFRESH_AWAIT = config["REFRESH_AWAIT"]
    BUY_BUTTON = 0
    REFRESH_BUTTON = 9
    SELL_BUTTON = 3

    SESSION_NAME = sys.argv[1] if len(sys.argv) > 1 else "default"
    SESSION_FOLDER = os.path.join("sessions", SESSION_NAME)
    SESSION_FILE = os.path.join(SESSION_FOLDER, f"{SESSION_NAME}.session")
    USER_CONFIG_FILE = os.path.join(SESSION_FOLDER, "config.json")

    if not os.path.exists(SESSION_FOLDER):
        os.makedirs(SESSION_FOLDER)

    if not os.path.exists(USER_CONFIG_FILE):
        shutil.copy2("sessions/default_config.json", USER_CONFIG_FILE)

    with open(USER_CONFIG_FILE, "r", encoding="utf-8") as f:
        user_config = json.load(f)

    CHANNELS = user_config["CHANNELS"]
    ALERTS_CHANNEL = user_config["ALERTS_CHANNEL"]
    MIN_REPUTATION = user_config["MIN_REPUTATION"]
    MIN_DEV_LOCK = user_config["MIN_DEV_LOCK"]
    BAN_WORDS = user_config["BAN_WORDS"]
    MAX_PROFIT_PERCENT = user_config["MAX_PROFIT_PERCENT"]
    MAX_LOSS_PERCENT = user_config["MAX_LOSS_PERCENT"]

load_config()

# Регулярные выражения
rep_pattern = re.compile(r"Rep:\s*`(\d+)\s*")
dev_lock_pattern = re.compile(r"Dev Lock:\s*`(\d+)h(\d+)m(\d+)s`")
link_pattern = re.compile(fr'https?://t.me/{BOT_USERNAME}\?start=([a-zA-Z0-9_]+)', re.IGNORECASE)
purchase_pattern = re.compile(r"Bought (\d+\.?\d*) (\w+) at an average price of (\d+\.\d+) for \$(\d+\.\d+)")
sold_pattern = re.compile(r"Sold (\d+\.?\d*) (\w+) at an average price of (\d+\.\d+) for \$(\d+\.\d+)")
value_pattern = re.compile(r"Value:\s+`([0-9]+\.[0-9]+)`")

# Инициализация клиента Telegram
client = TelegramClient(SESSION_FILE, API_ID, API_HASH)

# Отправка команды /start
async def send_start_command(bot_username, start_data):
    try:
        logger.info(f"Отправляем команду /start с данными: {start_data}")
        await client.send_message(bot_username, f"/start {start_data}")
        await asyncio.sleep(MESSAGE_AWAIT)  # Задержка после отправки команды
    except Exception as e:
        logger.error(f"Ошибка при отправке команды /start: {e}")
        await send_alert(f"❗️ Неудалось отправить команду /start\n\nПричина: {e}")

# Обработка ответа от бота
async def handle_bot_reply(bot_username, start_data):
    try:
        logger.info(f"Обрабатываем ответ от бота {bot_username} с данными: {start_data}")
        await send_start_command(bot_username, start_data)
        await asyncio.sleep(MESSAGE_AWAIT)

        async for bot_reply in client.iter_messages(bot_username, limit=1):
            if bot_reply.reply_markup:
                message_id = bot_reply.id
                await process_bot_reply(bot_reply, message_id)
            else:
                logger.info("Кнопки не найдены в ответе бота.")
                await send_alert("Кнопки не найдены в ответе бота")
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения от бота: {e}")
        await send_alert(f"❗️ Ошибка при обработке сообщения от бота\n\nПричина: {e}")

# Обработка кнопок в ответе бота
async def process_bot_reply(bot_reply, message_id):
    while True:
        try:
            await bot_reply.click(BUY_BUTTON)
            await asyncio.sleep(MESSAGE_AWAIT)  # Задержка после нажатия кнопки
            await process_purchase(bot_reply, message_id)
        except Exception as e:
            logger.error(f"Ошибка при нажатии кнопки BUY_BUTTON: {e}")

# Обработка сообщения о покупке
async def process_purchase(bot_reply, message_id):
    async for purchase_reply in client.iter_messages(BOT_USERNAME, limit=1):
        if purchase_match := purchase_pattern.search(purchase_reply.text):
            amount_bought = float(purchase_match.group(1))
            coin = purchase_match.group(2)
            price = float(purchase_match.group(3))
            total_cost = float(purchase_match.group(4))
            logger.info(f"Куплено: {amount_bought} {coin} по цене {price} за {total_cost}$")
            await send_alert(f"💰 Куплено: <b>{amount_bought} {coin}</b> по средней цене <b>{price}$</b> за <b>{total_cost}</b>\n\n")
            await monitor_value(bot_reply, message_id, total_cost)
        else:
            logger.info("Сообщение о покупке не найдено.")
            await send_alert("🔎 Сообщение о покупке не найдено.")
            await asyncio.sleep(1.5)

# Мониторинг значения Value
async def monitor_value(bot_reply, message_id, total_cost):
    max_profit = 0.0
    while True:
        await bot_reply.click(REFRESH_BUTTON)
        await asyncio.sleep(MESSAGE_AWAIT)  # Задержка после обновления
        updated_reply = await client.get_messages(BOT_USERNAME, ids=message_id)
        if value_match := value_pattern.search(updated_reply.text):
            current_value = float(value_match.group(1))
            await process_value(updated_reply, current_value, total_cost, max_profit)
        else:
            logger.info("Значение Value не найдено.")
            await send_alert("Значение Value не найдено")
        await asyncio.sleep(REFRESH_AWAIT)  # Задержка между проверками

# Обработка текущего значения Value
async def process_value(updated_reply, current_value, total_cost, max_profit):
    current_profit = current_value - total_cost
    logger.info(f"Текущее значение Value: {current_value} /// Профит: {current_profit:+.2f}$")
    max_profit = max(max_profit, current_profit)
    if current_value == 0.0:
        await handle_zero_value()
    elif current_value >= total_cost * (1 + MAX_PROFIT_PERCENT / 100):
        await sell_and_alert(updated_reply, "🤑", f"Цена выросла выше {MAX_PROFIT_PERCENT}%", current_profit)
    elif current_value <= total_cost * (1 + MAX_LOSS_PERCENT / 100):
        await sell_and_alert(updated_reply, "😰", f"Цена упала ниже {MAX_LOSS_PERCENT}%", current_profit)

# Обработка нулевого значения Value
async def handle_zero_value():
    logger.info("Value равно 0.0. Прекращаем проверку.")
    await send_alert("💸 Баланс равен <b>0.00$</b>. Прекращаем проверку.")
    await asyncio.sleep(MESSAGE_AWAIT)  # Задержка перед завершением
    async for sale_reply in client.iter_messages(BOT_USERNAME, limit=1):
        if sale_match := sold_pattern.search(sale_reply.text):
            await process_sale(sale_match, "😶", "Продажа была осуществлена вручную.")

# Продажа и отправка уведомления
async def sell_and_alert(updated_reply, emoji, reason, profit):
    await updated_reply.click(SELL_BUTTON)
    await asyncio.sleep(MESSAGE_AWAIT)  # Задержка после продажи
    async for sale_reply in client.iter_messages(BOT_USERNAME, limit=1):
        if sale_match := sold_pattern.search(sale_reply.text):
            await process_sale(sale_match, emoji, reason, profit)

# Обработка сообщения о продаже
async def process_sale(sale_match, emoji, reason, profit=None):
    amount_sold = float(sale_match.group(1))
    coin = sale_match.group(2)
    average_price = float(sale_match.group(3))
    total_sale_amount = float(sale_match.group(4))
    logger.info(f"Продано: {amount_sold} {coin} по средней цене {average_price} за {total_sale_amount}$")
    text = f"{emoji} Продано: <b>{amount_sold} {coin}</b> по средней цене <b>{average_price}$</b> за <b>{total_sale_amount}$</b>\n\n"
    if profit is not None:
        text += f"<blockquote>📈 {reason}. Прибыль: <b>{profit:+.2f}$</b></blockquote>\n"
    else:
        text += f"<blockquote>{reason}.</blockquote>\n"
    await send_alert(text)

# Отправка уведомления
async def send_alert(message):
    if not ALERTS_CHANNEL:
        return
    try:
        await client.send_message(ALERTS_CHANNEL, message, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления в канал {ALERTS_CHANNEL}: {e}")

# Мониторинг канала
async def monitor_channel(message):
    try:
        logger.info(f"Обрабатываем сообщение: {message.text}")
        entity = await client.get_entity(message.chat_id)

        if await check_ban_words(message):
            return

        if await check_reputation(message):
            return

        if await check_dev_lock(message):
            return

        if match := link_pattern.search(message.text):
            start_data = match.group(1)
            logger.info(f"Найдена ссылка, начинаем взаимодействие с ботом {BOT_USERNAME}, start_data: {start_data}")
            asyncio.create_task(handle_bot_reply(BOT_USERNAME, start_data))
        elif message.reply_markup:
            url = message.reply_markup.rows[0].buttons[0].url
            if url and link_pattern.match(url):
                logger.info(f"Найдена ссылка в первой кнопке, начинаем взаимодействие с ботом {BOT_USERNAME}, URL: {url}")
                start_data = url.split('start=')[-1]
                asyncio.create_task(handle_bot_reply(BOT_USERNAME, start_data))
            else:
                logger.info("Ссылка не соответствует паттерну или не найдена в первой кнопке")
                await send_alert(f"💥 Получено новое сообщение от канала <a href=\"https://t.me/c/{entity.id}/{message.id}\">{entity.title}</a>\n\n<blockquote>🔎 Ссылка в сообщении не найдена.</blockquote>\n")
        else:
            logger.info("Ссылка не найдена в сообщении")
            await send_alert(f"💥 Получено новое сообщение от канала <a href=\"https://t.me/c/{entity.id}/{message.id}\">{entity.title}</a>\n\n<blockquote>🔎 Ссылка в сообщении не найдена.</blockquote>\n")
    except Exception as e:
        logger.error(f"Ошибка при мониторинге канала: {e}")

# Проверка на запрещенные слова
async def check_ban_words(message):
    if BAN_WORDS.strip():
        ban_list = [word.strip().lower() for word in BAN_WORDS.split(",")]
        found_bad_word = next((bad_word for bad_word in ban_list if bad_word in message.text.lower()), None)
        if found_bad_word:
            logger.info(f"Сообщение содержит запрещённое слово: {found_bad_word}, пропускаем обработку")
            entity = await client.get_entity(message.chat_id)
            await send_alert(f"<b>💥 Получено новое сообщение от канала <a href=\"https://t.me/c/{entity.id}/{message.id}\">{entity.title}</a></b>\n\n<blockquote>🤬 Сообщение содержит запрещённое слово: <b>{found_bad_word}</b>, пропускаем обработку.</blockquote>\n")
            return True
    return False

# Проверка репутации
async def check_reputation(message):
    rep_match = rep_pattern.search(message.text)
    if rep_match and int(rep_match.group(1)) < MIN_REPUTATION:
        logger.info("Низкая репутация, пропускаем обработку")
        entity = await client.get_entity(message.chat_id)
        await send_alert(f"<b>💥 Получено новое сообщение от канала <a href=\"https://t.me/c/{entity.id}/{message.id}\">{entity.title}</a></b>\n\n<blockquote>👎 Низкая репутация создателя, пропускаем обработку.</blockquote>\n")
        return True
    return False

# Проверка Dev Lock
async def check_dev_lock(message):
    dev_lock_match = dev_lock_pattern.search(message.text)
    if dev_lock_match:
        min_dev_lock_pattern = re.compile(r"(\d+)h(\d+)m(\d+)s")
        min_dev_lock_match = min_dev_lock_pattern.search(MIN_DEV_LOCK)
        min_allowed_seconds = int(min_dev_lock_match.group(1)) * 3600 + int(min_dev_lock_match.group(2)) * 60 + int(min_dev_lock_match.group(3)) if min_dev_lock_match else 3600
        hours, minutes, seconds = map(int, dev_lock_match.groups())
        total_seconds = hours * 3600 + minutes * 60 + seconds
        if total_seconds <= min_allowed_seconds:
            logger.info(f"Dev Lock: {hours}h{minutes}m{seconds}s, пропускаем обработку")
            entity = await client.get_entity(message.chat_id)
            await send_alert(f"<b>💥 Получено новое сообщение от канала <a href=\"https://t.me/c/{entity.id}/{message.id}\">{entity.title}</a></b>\n\n<blockquote>⏳ Dev Lock: {hours}h{minutes}m{seconds}s, пропускаем обработку.</blockquote>\n")
            return True
    return False

# Запуск клиента
async def main():
    try:
        await client.start()
        logger.info(f"Бот запущен на сессии {SESSION_NAME} и ожидает сообщений...")
        await client.run_until_disconnected()
    except KeyboardInterrupt:
        logger.info("Получен сигнал завершения работы. Завершаем...")
        await client.disconnect()

# Обработка новых сообщений
@client.on(events.NewMessage(chats=CHANNELS))
async def on_message(event):
    logger.info(event)
    message = event.message
    logger.info(f"Новое сообщение от канала {event.chat_id}: {message.text}")
    asyncio.create_task(monitor_channel(message))

# Обработка команды !ping
@client.on(events.NewMessage(outgoing=True, pattern='!ping'))
async def handler(event):
    await event.respond('!pong')

# Запуск клиента
client.loop.run_until_complete(main())