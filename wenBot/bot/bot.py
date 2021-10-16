from wenBot.config.Config import Config, ENV
from wenBot.db.db import Database

import asyncio
import math
from typing import Union

import discord.utils
from discord.ext import commands


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

        if not math.isinf(timeout):
            await asyncio.sleep(timeout)
            await member.remove_roles(role)
            print(f'Action: Role {Config.PUNISHMENT_ROLE}removed for user {member}')

bot.run(ENV.TOKEN)
