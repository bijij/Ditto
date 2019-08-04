import asyncio
from io import BytesIO

from typing import Iterable

import discord
from discord.ext import commands


async def add_reactions(message: discord.Message, reactions: Iterable[discord.Emoji]):
    """Adds reactions to a message

    Args:
        message (discord.Message): The message to react to.
        reactions (): A set of reactions to add.
    """
    for reaction in reactions:
        asyncio.ensure_future(message.add_reaction(reaction))


async def fetch_previous_message(message: discord.Message) -> discord.Message:
    """Returns the message before the supplied message in chat.

    Args:
        message (discord.Message): The message afterwards.

    """
    async for _ in message.channel.history(before=message, limit=1):
        return _


async def download_attachment(message: discord.Message, *, index: int = 0) -> BytesIO:
    """Downloads the attachment at the specified index"""
    attachment = BytesIO()
    await message.attachments[index].save(attachment)
    return attachment


async def prompt(ctx: commands.Context, message: discord.Message, *, timeout=60, delete_after=True) -> bool:
    """Prompts the user for confirmation.

    Args:
        ctx (commands.Context): The command context to use.
        message (discord.Message): The message to initiate the prompt with.

    Kwargs:
        timeout (float): How long in seconts to wait before timing out.
            Default is 60 seconds.
        delete_after (bool): Determines wether the prompt should be deleted afterwards.
            Defaults to True.

    """
    confirm = False

    def check(payload):
        if payload.message_id == message.id and payload.user_id == ctx.author.id:
            if str(payload.emoji) in ['👍', '👎']:
                return True
        return False

    for emoji in ['👍', '👎']:
        await message.add_reaction(emoji)

    try:
        payload = await ctx.bot.wait_for('raw_reaction_add', check=check, timeout=timeout)
        if str(payload.emoji) == '👍':
            confirm = True

    finally:
        if delete_after:
            await message.delete()

        return confirm
