import os
from telethon import TelegramClient

def create_client(session_name, api_id, api_hash, session_dir="sessions"):
    """Создает и возвращает клиента, используя заданные параметры."""
    session_path = os.path.join(session_dir, session_name)
    
    # Убираем расширение .session, если оно есть
    if session_path.endswith(".session"):
        session_path = session_path[:-8]

    # Создаем папку для сессий, если её нет
    if not os.path.exists(session_dir):
        os.makedirs(session_dir)
    
    # Инициализируем клиента с путём к сессии
    client = TelegramClient(session_path, api_id, api_hash)

    return client
