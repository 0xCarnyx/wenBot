from dataclasses import dataclass
import os


@dataclass
class PunishedUser:
    member_id: int
    punishment_count: int
    last_ban: int


@dataclass
class ENV:
    TOKEN = os.environ.get("BOT_TOKEN")
