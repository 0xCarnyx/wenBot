import logging

from db import Database
from datastructures import ENV
import utils

from typing import Union
import time
import math

import regex as re

import discord.utils
from discord.ext import commands, tasks

config = utils.read_config()


logging.basicConfig(format="%(name)s - %(levelname)s - %(message)s")

bot = commands.Bot(command_prefix='/', description="This is wenBot 🤖")


@tasks.loop(seconds=2)
async def check_release():
    """Check every 30 seconds which users have done their time and can get released from timeout prison.
    This approach may seem less elegant than using only coroutines but it gracefully handles bot / server restarts."""
    for guild in bot.guilds:
        db = Database(config.get("DATABASE_FILENAME"))
        if punished_users := db.get_currently_punished_users(config["SECOND_OFFENSE_LIMIT"]):
            for punished_user in punished_users:
                user = await guild.fetch_member(punished_user.member_id)
                if releases_granted(punished_user.punishment_count, punished_user.last_ban):
                    db.set_unbanned(punished_user.member_id, guild.id)
                    role = discord.utils.get(guild.roles, name=config.get("PUNISHMENT_ROLE"))
                    await user.remove_roles(role)


@bot.command(name="grant-amnesty", pass_context=True)
async def grant_amnesty(context):
    """Allows users with a maintenance role to grant amnesty to all mentioned users. This will immediately remove the
    assigned role and remove the users entry from the timeout database.

    :param context: Context of the command
    """
    if any([discord.utils.get(context.message.author.roles, name=_role) for _role in config.get("MAINTENANCE_ROLES")]):
        mentioned_users = context.message.mentions
        for user in mentioned_users:
            db = Database(config.get("DATABASE_FILENAME"))
            db.remove_entry(user.id, context.guild.id)

            role = discord.utils.get(user.guild.roles, name=config.get("PUNISHMENT_ROLE"))
            await user.remove_roles(role)
        verb = "were" if len(mentioned_users) > 1 else "was"
        if mentioned_users:
            await context.send(f"{' '.join([_user.name for _user in mentioned_users])} {verb} granted amnesty.")


@bot.command(name="punish-wen", pass_context=True)
async def punish_wen(context):
    """Allows users with a maintenance role to manually punish users for violation of the rules.

    :param context: Context of the command
    """
    if any([discord.utils.get(context.message.author.roles, name=_role) for _role in config.get("MAINTENANCE_ROLES")]):
        mentioned_users = context.message.mentions
        for member in mentioned_users:
            timeout = determine_timeout(member.id, context.guild.id)

            role = discord.utils.get(member.guild.roles, name=config.get("PUNISHMENT_ROLE"))
            await member.add_roles(role)
            logging.info(f'Action: Role {config.get("PUNISHMENT_ROLE")} added for user {member}')

            if math.isinf(timeout):
                timeout_text = f"wen = ban. {member.name} muted forever."
            else:
                timeout_text = f"wen = ban. {member.name} muted for {int(timeout / 60)} minutes."
            await context.send(timeout_text)


def releases_granted(punishment_count: int, last_ban: int) -> bool:
    """Checks whether a user has done his time and can be released based on the configured limits.

    :param punishment_count: How often the user was already punished
    :param last_ban: Timestamp of the users latest ban
    :return: Whether the release request was granted
    """
    seconds_since_last_ban = int(time.time()) - last_ban

    if punishment_count == config.get("FIRST_OFFENSE_LIMIT"):
        if seconds_since_last_ban >= config.get("FIRST_OFFENSE_PENALTY"):
            return True
    elif config.get("FIRST_OFFENSE_LIMIT") < punishment_count <= config.get("SECOND_OFFENSE_LIMIT"):
        if seconds_since_last_ban >= config.get("SECOND_OFFENSE_PENALTY"):
            return True
    return False


def determine_timeout(member_id: int, guild_id: int) -> Union[int, float]:
    """Queries the connected database to determine the timeout the users deserves based on his timeout history.

    :param member_id: Discord ID of the member. Primary key of the associated timeout table.
    :param guild_id: Discord ID of the current guild.
    :return: How many minutes the user should be muted (through role assignment). Infinity if user shall be muted
    forever.
    """
    db = Database(config.get("DATABASE_FILENAME"))
    timeout = db.get_timeout(member_id, guild_id)

    if timeout is None:
        db.create_timeout_entry(member_id, guild_id)
        return config.get("FIRST_OFFENSE_PENALTY")

    updated_timeout = timeout + 1
    db.update_timeout(member_id, guild_id, updated_timeout)

    if updated_timeout == 1:
        return config.get("FIRST_OFFENSE_PENALTY")
    elif config.get("FIRST_OFFENSE_LIMIT") < updated_timeout <= config.get("SECOND_OFFENSE_LIMIT"):
        return config.get("SECOND_OFFENSE_PENALTY")
    elif updated_timeout > config.get("SECOND_OFFENSE_LIMIT"):
        return math.inf


def contains_banned_text(message: str) -> bool:
    """Uses regular expression patterns to check whether a message contains bannable text.

    :param message: lower cased message content
    :return: Whether the users deservers a ban or not
    """
    patterns = [r"\b(wen)\b",
                r"(^|\s)(when)(?:\s+\w+){1}(\s)*(?:\?)+($|\s)",
                r"(wen|when)\s(token|airdrop)($|\s)"]

    for pattern in patterns:
        if re.search(pattern, message):
            return True
    return False


@bot.listen("on_message")
async def on_message(message):
    """Listener which checks every message for rule violations and takes action if necessary

    :param message:
    """
    if message.author == bot.user or any([discord.utils.get(message.author.roles, name=_role)
                                          for _role in config.get("MAINTENANCE_ROLES")]):
        return

    message_channel = bot.get_channel(message.channel.id)

    if contains_banned_text(message.content.lower()):
        member = message.author

        timeout = determine_timeout(member.id, message.guild.id)

        role = discord.utils.get(member.guild.roles, name=config.get("PUNISHMENT_ROLE"))
        await member.add_roles(role)
        logging.info(f'Action: Role {config.get("PUNISHMENT_ROLE")} added for user {member}')

        if math.isinf(timeout):
            timeout_text = f"wen = ban. {member.name} muted forever."
        else:
            timeout_text = f"wen = ban. {member.name} muted for {int(timeout / 60)} minutes."
        await message_channel.send(timeout_text)

check_release.start()
bot.run(ENV.TOKEN)
