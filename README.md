# 🐰 Ayto HypurrFunBot

### Possibilities
- Working with multiple accounts with individual configurations
- Flexible configuration of tokens allowed for purchase
- Convenient setup of stop modes for sale

### Usage
- Download the repository and unzip it to a convenient location
- Customize the configuration files to suit your needs
- Install the required dependencies using the command `pip install requirements.txt`
- Run the bot using the command `py bot.py <session_name>`

### Setting up configurations
##### /config.json
Parameter        | Example                             | Description
-----------------|-------------------------------------|------------------------------------------------
APP_ID           | 0123456789                          | Telegram app api id
APP_HASH         | c87d83cbceb52b40a6ceff535741ebd3    | Telegram app api hash
BOT_USERNAME     | HypurrFunBot                        | HypurrFunBot username
MESSAGE_AWAIT    | 0.5                                 | Waiting for message to be received in seconds
REFRESH_AWAIT    | 2                                   | Delay between message updates

##### /sessions/default_config.json
Parameter              | Example            | Description
-----------------------|--------------------|-----------------------------------------------------------
CHANNELS               | HfunAlerts         | Comma separated list of channels
ALERTS_CHANNEL         | -1000000009        | Channel ID or username for notifications
MIN_REPUTATION         | 3                  | Minimum acceptable reputation of a token creator
MIN_DEV_LOCK           | 1h0m0s             | Minimum Dev Lock
BAN_WORDS              | test, testing      | List of prohibited words in the text separated by commas
STEP_PROFIT_PERCENT    | 5                  | Coming soon
MAX_PROFIT_PERCENT     | 30                 | Maximum profit percentage for sale
MIN_PROFIT_PERCENT     | -10                | Minimum profit percentage for sale
MAX_LOSS_PERCENT       | -10                | Coming soon
