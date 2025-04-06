<div align="center">
<img src="https://github.githubassets.com/images/icons/emoji/unicode/1f1f7-1f1fa.png"> <a href="https://github.com/ApTyp4uK1337/Auto-HypurrFunBot/blob/master/README.md" title="Версия на русском">Версия на русском</a>
</div>

# 🐰 Auto HypurrFunBot

Auto HypurrFunBot is an automated Telegram bot designed for channel monitoring and interaction with **[HypurrFunBot](https://t.me/HypurrFunBot)**.

## Features  
- Multi-account support with individual settings  
- Flexible configuration of available tokens for purchase  
- Convenient sale stop mode configuration  
- Work status notifications in Telegram channel  

## Installation & Launch  
1. Download the repository and extract to a preferred location.  
2. Configure the files according to your needs.  
3. Install required dependencies using:  
   ```sh
   pip install -r requirements.txt
   ```
4. Launch the bot with:  
   ```sh
   python bot.py <session_name>
   ```
   Where `<session_name>` matches a filename in the `sessions` folder.  

## Configuration  
##### `/config.json` (core parameters)  
| Parameter        | Example                             | Description                                           |
|-----------------|------------------------------------|----------------------------------------------------|
| `API_ID`        | `0123456789`                       | Telegram application API ID                         |
| `API_HASH`      | `c87d83cbceb52b40a6ceff535741ebd3` | Telegram application API Hash                       |
| `BOT_USERNAME`  | `HypurrFunBot`                     | HypurrFunBot username                               |
| `MESSAGE_AWAIT` | `0.5`                              | Message receiving delay (seconds)                  |
| `REFRESH_AWAIT` | `2`                                | Message update interval (seconds)                  |

##### `/sessions/default_config.json` (default session settings)  
##### `/sessions/<session_name>/config.json` (custom session settings)
| Parameter              | Example                           | Description                                                  |
|-----------------------|----------------------------------|-----------------------------------------------------------|
| `CHANNELS`            | `["HfunAlerts", -1000000000002]` | Channels to monitor (IDs or usernames)                    |
| `ALERTS_CHANNEL`      | `-10000000000001`                | Notifications channel (ID or username)                    |
| `MIN_REPUTATION`      | `3`                              | Minimum token creator reputation                          |
| `MIN_DEV_LOCK`        | `1h0m0s`                         | Minimum Dev Lock duration (developer lock time)           |
| `BAN_WORDS`           | `"test, testing, dont buy"`      | Blacklisted words in token descriptions                   |
| `MAX_PROFIT_PERCENT`  | `30`                             | Maximum profit percentage for auto-selling                |
| `MAX_LOSS_PERCENT`    | `-10`                            | Maximum loss percentage for auto-selling                 |

## Questions?
<a href="https://t.me/aptyp4uk1337"><img src="https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white" title="Telegram"></a>