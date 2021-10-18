# wenBot
Discord bot for the LevX DAO discord which bans the w word

## Getting started
Create a virtual environment and activate it
```
python -m venv venv
source venv/bin/activate
```
Install all necessary dependencies
```
pip install -r requirements.txt
```
Set the Discord bot token as env
```
export BOT_TOKEN=<InsertBotToken>
```
Configure the `config.yaml` to your likings and start the bot
```
python bot.py
```
Invite the bot to your server

## Deploying for constant uptime
* Use [supervisor](http://supervisord.org/running.html) (recommended)
* Use heroku or something similar if you don't have a VPS
* Start the script in a tmux session and disconnect (not recommended but works)

## Commands
The following commands can only be used by users which have a guild role set under `MAINTENANCE_ROLES` in the `config.yaml`
### /punish-wen
Punishes all mentioned users. Useful for cases where the bot doesn't automatically
picks up the w word.
#### Example
```
/punish wen @Foo @Bar
```
### /grant-amnesty
Grants complete amnesty to all mentioned users. Useful for false positives.
#### Example
```
/grant-amnesty @Foo @Bar
```

