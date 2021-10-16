from typing import Union
import logging
import time
from pathlib import Path

from dataclasses import dataclass
import math
import os

import discord.utils
from discord.ext import commands

import sqlite3
from sqlite3 import Error

logging.basicConfig(format="%(name)s - %(levelname)s - %(message)s")


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


class Database:
    def __init__(self, database):
        self.connection = self.create_db_connection(database)
        self.create_table()

    @staticmethod
    def create_db_connection(db_file: Path):
        """Creates a connection to a specified SQLite database file

        :param db_file: Path to the SQLite database file
        :return:
        """
        conn = None
        try:
            conn = sqlite3.connect(db_file)
            return conn
        except Error as e:
            logging.warning(e)

        return conn

    def create_table(self):
        """Creates wen_timeouts table in case it doesn't already exist

        :return:
        """
        statement = "CREATE TABLE IF NOT EXISTS wen_timeouts (member_id INTEGER PRIMARY KEY, counter INTEGER, last_ban INTEGER);"

        try:
            cursor = self.connection.cursor()
            cursor.execute(statement)
            self.connection.commit()
        except Error as e:
            logging.error(e)

    def execute(self, statement: str):
        try:
            cursor = self.connection.cursor()
            cursor.execute(statement)
            self.connection.commit()
        except Error as e:
            logging.error(e)

    def query(self, query: str, fetchall: bool):
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)

            if fetchall:
                return cursor.fetchall()
            return cursor.fetchone()

        except Error as e:
            logging.error(e)
            return

    def get_timeout(self, member_id: int) -> Union[None, int]:
        query = f"SELECT member_id, counter, last_ban FROM wen_timeouts WHERE member_id = {member_id};"
        result = self.query(query, False)
        if result is not None and len(result) > 0:
            return result[0]
        return

    def update_timeout(self, member_id: int, count: int):
        statement = f"UPDATE wen_timeouts SET count = {count + 1}, time = {int(time.time())} WHERE member_id = {member_id};"
        self.execute(statement)

    def create_timeout_entry(self, member_id: int):
        statement = f"INSERT INTO wen_timeouts VALUES ({member_id}, {1}, {int(time.time())});"
        self.execute(statement)

    def remove_entry(self, member_id: int):
        statement = f"DELETE FROM wen_timeouts WHERE member_id = {member_id}"
        self.execute(statement)


bot = commands.Bot(command_prefix='/', description="This is wenBot 🤖")


@bot.command(name="grant-amnesty", pass_context=True)
async def grant_amnesty(context):
    """Allows the admin to grant amnesty to n mentioned users. This will immediately remove the assigned role
    and remove the users entry from the timeout database.

    :param context: Context of the command
    :return:
    """
    if discord.utils.get(context.message.author.roles, name=Config.ADMIN_ROLE):
        mentioned_users = context.message.mentions
        for user in mentioned_users:
            db = Database(Config.DATABASE_FILENAME)
            db.remove_entry(user.id)

            role = discord.utils.get(user.guild.roles, name=Config.PUNISHMENT_ROLE)
            await user.remove_roles(role)
        await context.send(f"{' '.join([_user.name for _user in mentioned_users])} were granted amnesty.")


def determine_timeout(member_id: int) -> Union[int, float]:
    """Queries the connected database to determine the timeout the users deserves based on his timeout history.

    :param member_id: Discord ID of the member. Primary key of the associated timeout table.
    :return: How many minutes the user should be muted (through role assignment). Infinity if user shall be muted
    forever.
    """
    db = Database(Config.DATABASE_FILENAME)

    timeout = db.get_timeout(member_id)

    if not timeout:
        db.create_timeout_entry(member_id)
        return Config.FIRST_OFFENSE_PENALTY

    updated_timeout = timeout + 1
    db.update_timeout(member_id, updated_timeout)

    if Config.FIRST_OFFENSE_LIMIT < updated_timeout <= Config.SECOND_OFFENSE_LIMIT:
        return Config.SECOND_OFFENSE_PENALTY
    elif updated_timeout >= 5:
        return Config.LAST_OFFENSE_PENALTY


@bot.listen("on_message")
async def on_message(message):
    if message.author == bot.user or discord.utils.get(message.author.roles, name=Config.ADMIN_ROLE):
        return

    message_channel = bot.get_channel(message.channel.id)
    message_tokens = [msg.lower() for msg in message.content.split()]

    if 'wen' in message_tokens:
        member = message.author

        timeout = determine_timeout(member.id)

        role = discord.utils.get(member.guild.roles, name=Config.PUNISHMENT_ROLE)
        await member.add_roles(role)
        print(f'Action: Role {Config.PUNISHMENT_ROLE} added for user {member}')

        if math.isinf(timeout):
            timeout_text = f"wen = ban. {member.name} muted forever."
        else:
            timeout_text = f"wen = ban. {member.name} muted for {int(timeout / 60)} minutes."
        await message_channel.send(timeout_text)

bot.run(ENV.TOKEN)
