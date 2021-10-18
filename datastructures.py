from dataclasses import dataclass

from dotenv import dotenv_values

config = dotenv_values(".env")


@dataclass
class PunishedUser:
    member_id: int
    punishment_count: int
    last_ban: int


@dataclass
class ENV:
    TOKEN = config.get("BOT_TOKEN")
