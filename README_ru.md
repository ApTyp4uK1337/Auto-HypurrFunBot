<div align="center">
   <a href="https://github.com/ApTyp4uK1337/Auto-HypurrFunBot/blob/master/README.md" title="English version">:us: English version</a>
</div>

<div align="center">
   <img src="https://github.com/ApTyp4uK1337/Auto-HypurrFunBot/blob/master/assets/hypurrfunbot.png?raw=true" height="150" width="150">
</div>

# 🐰 Auto HypurrFunBot

Auto HypurrFunBot — это автоматизированный бот для Telegram, предназначенный для мониторинга каналов и взаимодействия с ботом **[HypurrFunBot](https://t.me/HypurrFunBot)**.

## Возможности  
- Поддержка нескольких аккаунтов с индивидуальными настройками  
- Гибкая настройка токенов, доступных для покупки  
- Удобная настройка режимов остановки продажи  
- Оповещения о работе в Telegram канал

## Установка и запуск  
1. Скачайте репозиторий и распакуйте его в удобное место.  
2. Настройте конфигурационные файлы под свои нужды.  
3. Установите необходимые зависимости с помощью команды:  
   ```sh
   pip install -r requirements.txt
   ```
4. Запустите бота командой:  
   ```sh
   python bot.py <session_name>
   ```
   Где `<session_name>` — имя сессии, соответствующее файлу в папке `sessions`.  

## Настройка конфигураций  
##### `/config.json` (основные параметры)  
| Параметр        | Пример                             | Описание                                           |
|-----------------|------------------------------------|----------------------------------------------------|
| `API_ID`        | `0123456789`                       | API ID Telegram-приложения                         |
| `API_HASH`      | `c87d83cbceb52b40a6ceff535741ebd3` | API Hash Telegram-приложения                       |
| `BOT_USERNAME`  | `HypurrFunBot`                     | Имя бота HypurrFunBot                              |
| `MESSAGE_AWAIT` | `0.5`                              | Ожидание получения сообщения (в секундах)          |
| `REFRESH_AWAIT` | `2`                                | Задержка между обновлениями сообщений (в секундах) |

##### `/sessions/default_config.json` (настройки сессий по умолчанию)  
##### `/sessions/<session_name>/config.json` (индивидуальная настройка сессии)
| Параметр              | Пример                           | Описание                                                  |
|-----------------------|----------------------------------|-----------------------------------------------------------|
| `CHANNELS`            | `["HfunAlerts", -1000000000002]` | Список каналов (ID или имена) для мониторинга             |
| `ALERTS_CHANNEL`      | `-10000000000001`                | Канал для уведомлений (ID или имя)                        |
| `MIN_REPUTATION`      | `3`                              | Минимальная репутация создателя токена                    |
| `MIN_DEV_LOCK`        | `1h0m0s`                         | Минимальный Dev Lock (время блокировки разработчиком)     |
| `BAN_WORDS`           | `"test, testing, dont buy"`      | Список запрещенных слов в тексте                          |
| `MAX_PROFIT_PERCENT`  | `30`                             | Максимальный процент прибыли для продажи                  |
| `MAX_LOSS_PERCENT`    | `-10`                            | Максимальный процент убытка для продажи                   |

## Остались вопросы?
<a href="https://t.me/aptyp4uk1337"><img src="https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white" title="Telegram"></a>