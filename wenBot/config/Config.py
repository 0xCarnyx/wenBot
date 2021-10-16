from dataclasses import dataclass
import math
import os


@dataclass
class Config:
    ADMIN_ROLE: str = "Wubba Lubba Dub Dub"
    PUNISHMENT_ROLE: str = "Where are my testicles?"

    FIRST_OFFENSE_PENALTY: int = 300
    FIRST_OFFENSE_LIMIT: int = 1
    SECOND_OFFENSE_PENALTY: int = 3600
    SECOND_OFFENSE_LIMIT: int = 4
    LAST_OFFENSE_PENALTY: float = math.inf

    DATABASE_FILENAME: str = "timeout.db"


@dataclass
class ENV:
    TOKEN = os.environ.get("BOT_TOKEN")
    DATABASE_URL = os.environ.get("DATABASE_URL")
