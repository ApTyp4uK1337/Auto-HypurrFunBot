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

with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

API_ID = config["APP_ID"]
API_HASH = config["APP_HASH"]
BOT_USERNAME = config["BOT_USERNAME"]
MESSAGE_AWAIT = config["MESSAGE_AWAIT"]
REFRESH_AWAIT = config["REFRESH_AWAIT"]
BUY_BUTTON = 0
REFRESH_BUTTON = 9
SELL_BUTTON = 4

if len(sys.argv) < 2:
    SESSION_NAME = "default"
else:
    SESSION_NAME = sys.argv[1]

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
MIN_PROFIT_PERCENT = user_config["MIN_PROFIT_PERCENT"]
STEP_PROFIT_PERCENT = user_config["STEP_PROFIT_PERCENT"]
MAX_LOSS_PERCENT = user_config["MAX_LOSS_PERCENT"]

client = TelegramClient(SESSION_FILE, API_ID, API_HASH)

# Регулярные выражения
rep_pattern = re.compile(r"Rep:\s*`(\d+)\s*")
dev_lock_pattern = re.compile(r"Dev Lock:\s*`(\d+)h(\d+)m(\d+)s`")
link_pattern = re.compile(fr'https?://t.me/{BOT_USERNAME}\?start=([a-zA-Z0-9_]+)', re.IGNORECASE)
purchase_pattern = re.compile(r"Bought (\d+\.?\d*) (\w+) at an average price of (\d+\.\d+) for \$(\d+\.\d+)")
sold_pattern = re.compile(r"Sold (\d+\.?\d*) (\w+) at an average price of (\d+\.\d+) for \$(\d+\.\d+)")
value_pattern = re.compile(r"Value:\s+`([0-9]+\.[0-9]+)`")


async def send_start_command(bot, bot_username, start_data):
    try:
        logger.info(f"Отправляем команду /start с данными: {start_data}")
        await bot.send_message(bot_username, f"/start {start_data}")
    except Exception as e:
        logger.error(f"Ошибка при отправке команды /start: {e}")


async def handle_bot_reply(user_bot, bot_username, start_data):
    try:
        logger.info(f"Обрабатываем ответ от бота {bot_username} с данными: {start_data}")

        await send_start_command(user_bot, bot_username, start_data)
        await asyncio.sleep(MESSAGE_AWAIT)

        # Получаем следующее сообщение от бота (которое должно содержать кнопки)
        async for bot_reply in user_bot.iter_messages(bot_username, limit=1):
            if bot_reply.reply_markup:
                message_id = bot_reply.id
                
                await bot_reply.click(BUY_BUTTON)
                await asyncio.sleep(MESSAGE_AWAIT)

                # Ожидаем сообщение о покупке
                async for purchase_reply in user_bot.iter_messages(bot_username, limit=1):
                    if purchase_match := purchase_pattern.search(purchase_reply.text):
                        amount_bought = float(purchase_match.group(1))
                        coin = purchase_match.group(2)
                        price = float(purchase_match.group(3))
                        total_cost = float(purchase_match.group(4))
                        logger.info(f"Куплено: {amount_bought} {coin} по цене {price} за {total_cost}$")

                        await send_alert(client, ALERTS_CHANNEL, f"Куплено: {amount_bought} {coin} по цене {price} за {total_cost}$")

                        max_profit = 0.0

                        while True:
                            await bot_reply.click(REFRESH_BUTTON)
                            await asyncio.sleep(MESSAGE_AWAIT)

                            updated_reply = await user_bot.get_messages(bot_username, ids=message_id)
                            if value_match := value_pattern.search(updated_reply.text):
                                current_value = float(value_match.group(1))

                                # Вычисляем текущий профит
                                current_profit = current_value - total_cost
                                logger.info(f"Текущее значение Value: {current_value} /// Профит: {current_profit:+.2f}$")

                                # Обновляем максимальный профит
                                max_profit = max(max_profit, current_profit)

                                if current_value == 0.0:
                                    # Закрываем при ручной продаже
                                    logger.info("Value равно 0.0. Прекращаем проверку.")

                                    await send_alert(client, ALERTS_CHANNEL, "Value равно 0.0. Прекращаем проверку")

                                    await asyncio.sleep(MESSAGE_AWAIT)

                                    async for sale_reply in user_bot.iter_messages(bot_username, limit=1):
                                        if sale_match := sold_pattern.search(sale_reply.text):
                                            amount_sold = float(sale_match.group(1))
                                            coin = sale_match.group(2)
                                            average_price = float(sale_match.group(3))
                                            total_sale_amount = float(sale_match.group(4))

                                            logger.info(f"Продано: {amount_sold} {coin} по средней цене {average_price} за {total_sale_amount}$")

                                            await send_alert(client, ALERTS_CHANNEL, f"Продано: {amount_sold} {coin} по средней цене {average_price} за {total_sale_amount}$")

                                    return
                                elif current_value >= total_cost * (1 + MAX_PROFIT_PERCENT / 100):
                                    # Жмем кнопку Sell
                                    await updated_reply.click(SELL_BUTTON)

                                    await asyncio.sleep(MESSAGE_AWAIT)

                                    async for sale_reply in user_bot.iter_messages(bot_username, limit=1):
                                        if sale_match := sold_pattern.search(sale_reply.text):
                                            amount_sold = float(sale_match.group(1))
                                            coin = sale_match.group(2)
                                            average_price = float(sale_match.group(3))
                                            total_sale_amount = float(sale_match.group(4))

                                            logger.info(f"Продано: {amount_sold} {coin} по средней цене {average_price} за {total_sale_amount}$")

                                            await send_alert(client, ALERTS_CHANNEL, f"Продано: {amount_sold} {coin} по средней цене {average_price} за {total_sale_amount}$")

                                            final_profit = total_sale_amount - total_cost

                                            logger.info(f"Value превышает {MAX_PROFIT_PERCENT}%. Профит: {final_profit:+.2f}$")

                                    return
                                elif current_value <= total_cost * (1 + MAX_LOSS_PERCENT / 100):
                                    # Жмем кнопку Sell
                                    await updated_reply.click(SELL_BUTTON)

                                    await asyncio.sleep(MESSAGE_AWAIT)

                                    async for sale_reply in user_bot.iter_messages(bot_username, limit=1):
                                        if sale_match := sold_pattern.search(sale_reply.text):
                                            amount_sold = float(sale_match.group(1))
                                            coin = sale_match.group(2)
                                            average_price = float(sale_match.group(3))
                                            total_sale_amount = float(sale_match.group(4))

                                            logger.info(f"Продано: {amount_sold} {coin} по средней цене {average_price} за {total_sale_amount}$")

                                            await send_alert(client, ALERTS_CHANNEL, f"Продано: {amount_sold} {coin} по средней цене {average_price} за {total_sale_amount}$")

                                            final_loss = total_sale_amount - total_cost

                                            logger.info(f"Value упало ниже {MAX_LOSS_PERCENT}%. Убыток: {final_loss:+.2f}$")

                                    return

                                last_value = current_value
                            else:
                                logger.info("Значение Value не найдено.")

                                await send_alert(client, ALERTS_CHANNEL, "Значение Value не найдено")

                            await asyncio.sleep(REFRESH_AWAIT)
                    else:
                        logger.info("Сообщение о покупке не найдено.")

                        await send_alert(client, ALERTS_CHANNEL, "Сообщение о покупке не найдено")
            else:
                logger.info("Кнопки не найдены в ответе бота.")

                await send_alert(client, ALERTS_CHANNEL, "Кнопки не найдены в ответе бота")
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения от бота: {e}")

        await send_alert(client, ALERTS_CHANNEL, "Ошибка при обработке сообщения от бота")


async def monitor_channel(client, message):
    try:
        logger.info(f"Обрабатываем сообщение: {message.text}")

        entity = await client.get_entity(message.chat_id)

        if BAN_WORDS.strip():
            ban_list = [word.strip().lower() for word in BAN_WORDS.split(",")]

            found_bad_word = next((bad_word for bad_word in ban_list if bad_word in message.text.lower()), None)

            if found_bad_word:
                logger.info(f"Сообщение содержит запрещённое слово: {found_bad_word}, пропускаем обработку")

                text = f"<b>💥 Получено новое сообщение от канала <a href=\"https://t.me/c/{entity.id}/{message.id}\">{entity.title}</a></b>\n\n"
                text += f"<blockquote>🤬 Сообщение содержит запрещённое слово: <b>{found_bad_word}</b>, пропускаем обработку.</blockquote>\n"

                await send_alert(client, ALERTS_CHANNEL, text)

                return

        rep_match = rep_pattern.search(message.text)

        if rep_match and int(rep_match.group(1)) < MIN_REPUTATION:
            logger.info("Низкая репутация, пропускаем обработку")

            text = f"<b>💥 Получено новое сообщение от канала <a href=\"https://t.me/c/{entity.id}/{message.id}\">{entity.title}</a></b>\n\n"
            text += f"<blockquote>👎 Низкая репутация создателя, пропускаем обработку.</blockquote>\n"

            await send_alert(client, ALERTS_CHANNEL, text)

            return

        dev_lock_match = dev_lock_pattern.search(message.text)

        if dev_lock_match:
            min_dev_lock_pattern = re.compile(r"(\d+)h(\d+)m(\d+)s")
            min_dev_lock_match = min_dev_lock_pattern.search(MIN_DEV_LOCK)

            if min_dev_lock_match:
                hours, minutes, seconds = map(int, min_dev_lock_match.groups())
                min_allowed_seconds = hours * 3600 + minutes * 60 + seconds
            else:
                min_allowed_seconds = 1 * 3600

            hours, minutes, seconds = map(int, dev_lock_match.groups())
            total_seconds = hours * 3600 + minutes * 60 + seconds

            if total_seconds <= min_allowed_seconds:
                logger.info(f"Dev Lock: {hours}h{minutes}m{seconds}s, пропускаем обработку")

                text = f"<b>💥 Получено новое сообщение от канала <a href=\"https://t.me/c/{entity.id}/{message.id}\">{entity.title}</a></b>\n\n"
                text += f"<blockquote>⏳ Dev Lock: {hours}h{minutes}m{seconds}s, пропускаем обработку.</blockquote>\n"

                await send_alert(client, ALERTS_CHANNEL, text)

                return

        match = link_pattern.search(message.text)

        if match:
            start_data = match.group(1)
            logger.info(f"Найдена ссылка, начинаем взаимодействие с ботом {BOT_USERNAME}, start_data: {start_data}")
            asyncio.create_task(handle_bot_reply(client, BOT_USERNAME, start_data))
        elif message.reply_markup:
            url = message.reply_markup.rows[0].buttons[0].url

            if url and link_pattern.match(url):
                logger.info(f"Найдена ссылка в первой кнопке, начинаем взаимодействие с ботом {BOT_USERNAME}, URL: {url}")
                start_data = url.split('start=')[-1]
                asyncio.create_task(handle_bot_reply(client, BOT_USERNAME, start_data))
            else:
                logger.info(url)
                logger.info("Ссылка не соответствует паттерну или не найдена в первой кнопке")

                text = f"<b>💥 Получено новое сообщение от канала <a href=\"https://t.me/c/{entity.id}/{message.id}\">{entity.title}</a></b>\n\n"
                text += f"<blockquote>🔎 Ссылка в сообщении не найдена.</blockquote>\n"

                await send_alert(client, ALERTS_CHANNEL, text)
        else:
            logger.info("Ссылка не найдена в сообщении")

            text = f"<b>💥 Получено новое сообщение от канала <a href=\"https://t.me/c/{entity.id}/{message.id}\">{entity.title}</a></b>\n\n"
            text += f"<blockquote>🔎 Ссылка в сообщении не найдена.</blockquote>\n"

            await send_alert(client, ALERTS_CHANNEL, text)
    except Exception as e:
        logger.error(f"Ошибка при мониторинге канала: {e}")


async def send_alert(client, channel_id, message):
    if not channel_id:
        return
    try:
        await client.send_message(channel_id, message, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления в канал {channel_id}: {e}")

CHANNELS_LIST = [ch.strip() for ch in CHANNELS.split(",")]


@client.on(events.NewMessage(chats=CHANNELS_LIST))
async def on_message(event):
    message = event.message
    logger.info(f"Новое сообщение от канала {event.chat_id}: {message.text}")
    asyncio.create_task(monitor_channel(client, message))


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