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
        return json.load(f)

config = load_config()

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

# Инициализация папки сессии и конфигурации пользователя
def initialize_session():
    if not os.path.exists(SESSION_FOLDER):
        os.makedirs(SESSION_FOLDER)
    if not os.path.exists(USER_CONFIG_FILE):
        shutil.copy2("sessions/default_config.json", USER_CONFIG_FILE)

initialize_session()

# Загрузка пользовательской конфигурации
def load_user_config():
    with open(USER_CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

user_config = load_user_config()

CHANNELS = user_config["CHANNELS"]
ALERTS_CHANNEL = user_config["ALERTS_CHANNEL"]
MIN_REPUTATION = user_config["MIN_REPUTATION"]
MIN_DEV_LOCK = user_config["MIN_DEV_LOCK"]
BAN_WORDS = user_config["BAN_WORDS"]
MAX_PROFIT_PERCENT = user_config["MAX_PROFIT_PERCENT"]
MAX_LOSS_PERCENT = user_config["MAX_LOSS_PERCENT"]

# Регулярные выражения
PATTERNS = {
    "rep": re.compile(r"Rep:\s*`(\d+)\s*"),
    "dev_lock": re.compile(r"Dev Lock:\s*`(\d+)h(\d+)m(\d+)s`"),
    "link": re.compile(fr'https?://t.me/{BOT_USERNAME}\?start=([a-zA-Z0-9_]+)', re.IGNORECASE),
    "purchase": re.compile(r"Bought (\d+\.?\d*) (\w+) at an average price of (\d+\.\d+) for \$(\d+\.\d+)"),
    "sold": re.compile(r"Sold (\d+\.?\d*) (\w+) at an average price of (\d+\.\d+) for \$(\d+\.\d+)"),
    "value": re.compile(r"Value:\s+`([0-9]+\.[0-9]+)`")
}

client = TelegramClient(SESSION_FILE, API_ID, API_HASH)


async def send_start_command(bot, bot_username, start_data):
    try:
        logger.info(f"Отправляем команду /start с данными: {start_data}")
        await bot.send_message(bot_username, f"/start {start_data}")
    except Exception as e:
        logger.error(f"Ошибка при отправке команды /start: {e}")

        text = "<b>❗️ Неудалось отправить команду /start</b>\n\n"
        text += f"<blockquoute>Причина: {e}</blockquote>\n"

        await send_alert(client, ALERTS_CHANNEL, text)


async def handle_bot_reply(user_bot, bot_username, start_data):
    try:
        logger.info(f"Обрабатываем ответ от бота {bot_username} с данными: {start_data}")

        await send_start_command(user_bot, bot_username, start_data)
        await asyncio.sleep(MESSAGE_AWAIT)

        async for bot_reply in user_bot.iter_messages(bot_username, limit=1):
            if bot_reply.reply_markup:
                await process_bot_reply(user_bot, bot_username, bot_reply)
            else:
                logger.info("Кнопки не найдены в ответе бота.")
                await send_alert(client, ALERTS_CHANNEL, "Кнопки не найдены в ответе бота")
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения от бота: {e}")
        await send_alert(client, ALERTS_CHANNEL, "Ошибка при обработке сообщения от бота")


async def process_bot_reply(user_bot, bot_username, bot_reply):
    message_id = bot_reply.id

    await bot_reply.click(BUY_BUTTON)
    await asyncio.sleep(MESSAGE_AWAIT)

    async for purchase_reply in user_bot.iter_messages(bot_username, limit=1):
        if purchase_match := PATTERNS["purchase"].search(purchase_reply.text):
            await process_purchase(user_bot, bot_username, bot_reply, purchase_match, message_id)
        else:
            logger.info("Сообщение о покупке не найдено.")

            await send_alert(client, ALERTS_CHANNEL, "🔎 Сообщение о покупке не найдено.")


async def process_purchase(user_bot, bot_username, bot_reply, purchase_match, message_id):
    amount_bought = float(purchase_match.group(1))
    coin = purchase_match.group(2)
    price = float(purchase_match.group(3))
    total_cost = float(purchase_match.group(4))
    logger.info(f"Куплено: {amount_bought} {coin} по цене {price} за {total_cost}$")

    text = f"💰 Куплено: <b>{amount_bought} {coin}</b> по средней цене <b>{price}$</b> за <b>{total_cost}</b>\n\n"
    await send_alert(client, ALERTS_CHANNEL, text)

    while True:
        await bot_reply.click(REFRESH_BUTTON)
        await asyncio.sleep(MESSAGE_AWAIT)

        updated_reply = await user_bot.get_messages(bot_username, ids=message_id)
        if value_match := PATTERNS["value"].search(updated_reply.text):
            await process_value(user_bot, bot_username, updated_reply, value_match, total_cost)
        else:
            logger.info("Значение Value не найдено.")
            await send_alert(client, ALERTS_CHANNEL, "Значение Value не найдено")
        await asyncio.sleep(REFRESH_AWAIT)


async def process_value(user_bot, bot_username, updated_reply, value_match, total_cost):
    max_profit = 0.0
    current_value = float(value_match.group(1))
    current_profit = current_value - total_cost
    logger.info(f"Текущее значение Value: {current_value} /// Профит: {current_profit:+.2f}$")
    max_profit = max(max_profit, current_profit)

    if current_value == 0.0:
        await handle_zero_value(user_bot, bot_username, total_cost)
        return
    elif current_value >= total_cost * (1 + MAX_PROFIT_PERCENT / 100):
        await sell_and_alert(user_bot, bot_username, updated_reply, "🤑", MAX_PROFIT_PERCENT, current_profit)
        return
    elif current_value <= total_cost * (1 + MAX_LOSS_PERCENT / 100):
        await sell_and_alert(user_bot, bot_username, updated_reply, "😰", MAX_LOSS_PERCENT, current_profit)
        return


async def handle_zero_value(user_bot, bot_username, total_cost):
    logger.info("Value равно 0.0. Прекращаем проверку.")
    text = f"💸 Баланс равен 0.00$. Прекращаем проверку.\n\n"
    await send_alert(client, ALERTS_CHANNEL, text)

    await asyncio.sleep(MESSAGE_AWAIT)
    async for sale_reply in user_bot.iter_messages(bot_username, limit=1):
        if sale_match := PATTERNS["sold"].search(sale_reply.text):
            await process_sale(sale_match, "😶", "Продажа была осуществлена вручную.")


async def sell_and_alert(user_bot, bot_username, updated_reply, emoji, percent, profit):
    await updated_reply.click(SELL_BUTTON)
    await asyncio.sleep(MESSAGE_AWAIT)

    async for sale_reply in user_bot.iter_messages(bot_username, limit=1):
        if sale_match := PATTERNS["sold"].search(sale_reply.text):
            await process_sale(sale_match, emoji, f"Цена изменилась на {percent}%. Прибыль: {profit:+.2f}$")


async def process_sale(sale_match, emoji, comment):
    amount_sold = float(sale_match.group(1))
    coin = sale_match.group(2)
    average_price = float(sale_match.group(3))
    total_sale_amount = float(sale_match.group(4))

    logger.info(f"Продано: {amount_sold} {coin} по средней цене {average_price} за {total_sale_amount}$")
    text = f"{emoji} Продано: <b>{amount_sold} {coin}</b> по средней цене <b>{average_price}$</b> за <b>{total_sale_amount}</b>\n\n"
    text += f"<blockquote>{comment}</blockquote>\n"
    await send_alert(client, ALERTS_CHANNEL, text)


async def monitor_channel(client, message):
    try:
        logger.info(f"Обрабатываем сообщение: {message.text}")
        entity = await client.get_entity(message.chat_id)

        if BAN_WORDS.strip():
            ban_list = [word.strip().lower() for word in BAN_WORDS.split(",")]

            if any(bad_word in message.text.lower() for bad_word in ban_list):
                await handle_ban_word(entity, message, ban_list)
                return

        if rep_match := PATTERNS["rep"].search(message.text):
            if int(rep_match.group(1)) < MIN_REPUTATION:
                await handle_low_reputation(entity, message)
                return

        if dev_lock_match := PATTERNS["dev_lock"].search(message.text):
            if is_dev_lock_too_low(dev_lock_match):
                await handle_low_dev_lock(entity, message, dev_lock_match)
                return

        if match := PATTERNS["link"].search(message.text):
            await handle_link_match(client, match)
        elif message.reply_markup:
            await handle_reply_markup(client, message, entity)
        else:
            await handle_no_link(entity, message)
    except Exception as e:
        logger.error(f"Ошибка при мониторинге канала: {e}")


async def handle_ban_word(entity, message, ban_list):
    found_bad_word = next((bad_word for bad_word in ban_list if bad_word in message.text.lower()), None)
    logger.info(f"Сообщение содержит запрещённое слово: {found_bad_word}, пропускаем обработку")
    text = f"<b>💥 Получено новое сообщение от канала <a href=\"https://t.me/c/{entity.id}/{message.id}\">{entity.title}</a></b>\n\n"
    text += f"<blockquote>🤬 Сообщение содержит запрещённое слово: <b>{found_bad_word}</b>, пропускаем обработку.</blockquote>\n"
    await send_alert(client, ALERTS_CHANNEL, text)


async def handle_low_reputation(entity, message):
    logger.info("Низкая репутация, пропускаем обработку")
    text = f"<b>💥 Получено новое сообщение от канала <a href=\"https://t.me/c/{entity.id}/{message.id}\">{entity.title}</a></b>\n\n"
    text += f"<blockquote>👎 Низкая репутация создателя, пропускаем обработку.</blockquote>\n"
    await send_alert(client, ALERTS_CHANNEL, text)


def is_dev_lock_too_low(dev_lock_match):
    hours, minutes, seconds = map(int, dev_lock_match.groups())
    total_seconds = hours * 3600 + minutes * 60 + seconds
    min_allowed_seconds = get_min_allowed_seconds()
    
    return total_seconds <= min_allowed_seconds


def get_min_allowed_seconds():
    min_dev_lock_pattern = re.compile(r"(\d+)h(\d+)m(\d+)s")
    min_dev_lock_match = min_dev_lock_pattern.search(MIN_DEV_LOCK)

    if min_dev_lock_match:
        hours, minutes, seconds = map(int, min_dev_lock_match.groups())
        return hours * 3600 + minutes * 60 + seconds
    
    return 1 * 3600


async def handle_low_dev_lock(entity, message, dev_lock_match):
    hours, minutes, seconds = map(int, dev_lock_match.groups())
    logger.info(f"Dev Lock: {hours}h{minutes}m{seconds}s, пропускаем обработку")
    text = f"<b>💥 Получено новое сообщение от канала <a href=\"https://t.me/c/{entity.id}/{message.id}\">{entity.title}</a></b>\n\n"
    text += f"<blockquote>⏳ Dev Lock: {hours}h{minutes}m{seconds}s, пропускаем обработку.</blockquote>\n"
    await send_alert(client, ALERTS_CHANNEL, text)


async def handle_link_match(client, match):
    start_data = match.group(1)
    logger.info(f"Найдена ссылка, начинаем взаимодействие с ботом {BOT_USERNAME}, start_data: {start_data}")
    asyncio.create_task(handle_bot_reply(client, BOT_USERNAME, start_data))


async def handle_reply_markup(client, message, entity):
    url = message.reply_markup.rows[0].buttons[0].url
    if url and PATTERNS["link"].match(url):
        logger.info(f"Найдена ссылка в первой кнопке, начинаем взаимодействие с ботом {BOT_USERNAME}, URL: {url}")
        start_data = url.split('start=')[-1]
        asyncio.create_task(handle_bot_reply(client, BOT_USERNAME, start_data))
    else:
        logger.info(url)
        logger.info("Ссылка не соответствует паттерну или не найдена в первой кнопке")
        text = f"<b>💥 Получено новое сообщение от канала <a href=\"https://t.me/c/{entity.id}/{message.id}\">{entity.title}</a></b>\n\n"
        text += f"<blockquote>🔎 Ссылка в сообщении не найдена.</blockquote>\n"
        await send_alert(client, ALERTS_CHANNEL, text)


async def handle_no_link(entity, message):
    logger.info("Ссылка не найдена в сообщении")
    text = f"<b>💥 Получено новое сообщение от канала <a href=\"https://t.me/c/{entity.id}/{message.id}\">{entity.title}</a></b>\n\n"
    text += f"<blockquote>🔎 Ссылка в сообщении не найдена.</blockquote>\n"
    await send_alert(client, ALERTS_CHANNEL, text)


async def send_alert(client, channel_id, message):
    if not channel_id:
        return
    try:
        await client.send_message(channel_id, message, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления в канал {channel_id}: {e}")


@client.on(events.NewMessage(chats=CHANNELS))
async def on_message(event):
    message = event.message
    logger.info(f"Новое сообщение от канала {event.chat_id}: {message.text}")
    asyncio.create_task(monitor_channel(client, message))


@client.on(events.NewMessage(outgoing=True, pattern='!ping'))
async def handler(event):
    await event.respond('!pong')


async def main():
    try:
        await client.start()
        logger.info(f"Бот запущен на сессии {SESSION_NAME} и ожидает сообщений...")
        await client.run_until_disconnected()
    except KeyboardInterrupt:
        logger.info("Получен сигнал завершения работы. Завершаем...")
        await client.disconnect()


# Запускаем клиента
client.loop.run_until_complete(main())