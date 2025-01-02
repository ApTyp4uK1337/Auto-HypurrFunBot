import os
import asyncio
import re
import logging
from telethon import TelegramClient, events
from config import load_config

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загружаем конфигурацию
config = load_config()

# Извлекаем параметры из конфигурации
API_ID = config["API_ID"]
API_HASH = config["API_HASH"]
SESSION_NAME = config["SESSION_NAME"]
CHANNEL = config["CHANNEL"]
BOT_USERNAME = config["BOT_USERNAME"]
STEP_PROFIT_PERCENT = config["STEP_PROFIT_PERCENT"]
MAX_PROFIT_PERCENT = config["MAX_PROFIT_PERCENT"]
MIN_PROFIT_PERCENT = config["MIN_PROFIT_PERCENT"]
MAX_LOSS_PERCENT = config["MAX_LOSS_PERCENT"]

BUY_BUTTON = 0
REFRESH_BUTTON = 9
SELL_BUTTON = 4

if not os.path.exists('sessions'):
    os.makedirs('sessions')

# Создаем клиента
client = TelegramClient(f"sessions/{SESSION_NAME}", API_ID, API_HASH)

# Регулярные выражения
link_pattern = fr'http://t.me/{BOT_USERNAME}\?start=([a-zA-Z0-9_]+)'
purchase_pattern = r"Bought (\d+\.?\d*) (\w+) at an average price of (\d+\.\d+) for \$(\d+\.\d+)"
sold_pattern = r"Sold (\d+\.?\d*) (\w+) at an average price of (\d+\.\d+) for \$(\d+\.\d+)"
value_pattern = r"Value:\s+`([0-9]+\.[0-9]+)`"

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
        await asyncio.sleep(1)

        # Получаем следующее сообщение от бота (которое должно содержать кнопки)
        async for bot_reply in user_bot.iter_messages(bot_username, limit=1):
            if bot_reply.reply_markup:
                message_id = bot_reply.id
                await bot_reply.click(BUY_BUTTON)
                await asyncio.sleep(1)

                # Ожидаем сообщение о покупке
                async for purchase_reply in user_bot.iter_messages(bot_username, limit=1):
                    if purchase_match := re.search(purchase_pattern, purchase_reply.text):
                        amount_bought = float(purchase_match.group(1))
                        coin = purchase_match.group(2)
                        price = float(purchase_match.group(3))
                        total_cost = float(purchase_match.group(4))
                        logger.info(f"Куплено: {amount_bought} {coin} по цене {price} за {total_cost}$")
                        
                        max_profit = 0.0
                        
                        while True:
                            await bot_reply.click(REFRESH_BUTTON) # Жмем Refresh
                            await asyncio.sleep(1)

                            updated_reply = await user_bot.get_messages(bot_username, ids=message_id)
                            if value_match := re.search(value_pattern, updated_reply.text):
                                current_value = float(value_match.group(1))
                                
                                # Вычисляем текущий профит
                                current_profit = current_value - total_cost
                                logger.info(f"Текущее значение Value: {current_value} /// Профит: {current_profit:+.2f}$")
                                
                                # Обновляем максимальный профит
                                max_profit = max(max_profit, current_profit)

                                if current_value == 0.0:
                                    # Закрываем при ручной продаже
                                    logger.info("Value равно 0.0. Прекращаем проверку.")
                                    
                                    await asyncio.sleep(1)
                                    
                                    async for sale_reply in user_bot.iter_messages(bot_username, limit=1):
                                        if sale_match := re.search(sold_pattern, sale_reply.text):
                                            amount_sold = float(sale_match.group(1))
                                            coin = sale_match.group(2)
                                            average_price = float(sale_match.group(3))
                                            total_sale_amount = float(sale_match.group(4))
                                            
                                            logger.info(f"Продано: {amount_sold} {coin} по средней цене {average_price} за {total_sale_amount}$")
                                            
                                    return
                                elif current_value >= total_cost * (1 + MAX_PROFIT_PERCENT / 100):
                                    await updated_reply.click(SELL_BUTTON) # Жмем кнопку Sell
                                    
                                    await asyncio.sleep(1)
                                    
                                    async for sale_reply in user_bot.iter_messages(bot_username, limit=1):
                                        if sale_match := re.search(sold_pattern, sale_reply.text):
                                            amount_sold = float(sale_match.group(1))
                                            coin = sale_match.group(2)
                                            average_price = float(sale_match.group(3))
                                            total_sale_amount = float(sale_match.group(4))
                                            
                                            logger.info(f"Продано: {amount_sold} {coin} по средней цене {average_price} за {total_sale_amount}$")
                                            
                                            final_profit = total_sale_amount - total_cost
                                            
                                            logger.info(f"Value превышает {MAX_PROFIT_PERCENT}%. Профит: {final_profit:+.2f}$")
                                            
                                    return
                                elif current_value <= total_cost * (1 + MAX_LOSS_PERCENT / 100):
                                    await updated_reply.click(SELL_BUTTON) # Жмем кнопку Sell
                                    
                                    await asyncio.sleep(1)
                                    
                                    async for sale_reply in user_bot.iter_messages(bot_username, limit=1):
                                        if sale_match := re.search(sold_pattern, sale_reply.text):
                                            amount_sold = float(sale_match.group(1))
                                            coin = sale_match.group(2)
                                            average_price = float(sale_match.group(3))
                                            total_sale_amount = float(sale_match.group(4))
                                            
                                            logger.info(f"Продано: {amount_sold} {coin} по средней цене {average_price} за {total_sale_amount}$")
                                            
                                            final_loss = total_sale_amount - total_cost
                                            
                                            logger.info(f"Value упало ниже {MAX_LOSS_PERCENT}%. Убыток: {final_loss:+.2f}$")
                                            
                                    return
                            else:
                                logger.info("Значение Value не найдено.")
                                    
                            await asyncio.sleep(2)
                    else:
                        logger.info("Сообщение о покупке не найдено.")
            else:
                logger.info("Кнопки не найдены в ответе бота.")
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения от бота: {e}")

async def monitor_channel(message):
    try:
        logger.info(f"Обрабатываем сообщение: {message.text}")
        match = re.search(link_pattern, message.text)
        if match:
            start_data = match.group(1)
            logger.info(f"Найдена ссылка, начинаем взаимодействие с ботом {BOT_USERNAME}, start_data: {start_data}")
            asyncio.create_task(handle_bot_reply(client, BOT_USERNAME, start_data))
        else:
            logger.info("Ссылка не найдена в сообщении")
    except Exception as e:
        logger.error(f"Ошибка при мониторинге канала: {e}")


@client.on(events.NewMessage(chats=CHANNEL))
async def on_message(event):
    message = event.message
    logger.info(f"Новое сообщение от канала {CHANNEL}: {message.text}")
    asyncio.create_task(monitor_channel(message))

# Запускаем клиента
logger.info(f"Бот запущен на сессии {SESSION_NAME} и слушает канал {CHANNEL}...")
client.start()
client.run_until_disconnected()
