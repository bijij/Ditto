from asyncio import ensure_future
from io import BytesIO
from typing import Iterable

import discord


__all__ = [
    'RawMessage',
    'add_reactions', 'fetch_previous_message', 'delete_message',
    'download_attachment', 'download_avatar'
]


class RawMessage(discord.Message):
    """Stateless Discord Message object.

    Args:
        client (discord.Client): The client which will alter the message.
        channel (discord.TextChannel): The channel the message is in.
        message_id (int): The message's ID.
    """

    def __init__(self, client, channel, message_id):
        self._state = client._connection
        self.id = message_id
        self.channel = channel

    def __repr__(self):
        return f"<RawMessage id={self.id} channel={self.channel}>"


async def add_reactions(message: discord.Message, reactions: Iterable[discord.Emoji]):
    """Adds reactions to a message

    Args:
        message (discord.Message): The message to react to.
        reactions (): A set of reactions to add.
    """
    async def react():
        for reaction in reactions:
            await message.add_reaction(reaction)

    ensure_future(react())


async def fetch_previous_message(message: discord.Message) -> discord.Message:
    """Returns the message before the supplied message in chat.

    Args:
        message (discord.Message): The message afterwards.

    """
    async for _ in message.channel.history(before=message, limit=1):
        return _


async def delete_message(message: discord.Message) -> bool:
    """Attempts to delete the provided message"""
    try:
        await message.delete()
        return True
    except (discord.Forbidden, discord.NotFound):
        return False


async def download_attachment(message: discord.Message, *, index: int = 0) -> BytesIO:
    """Downloads the attachment at the specified index."""
    attachment = BytesIO()
    await message.attachments[index].save(attachment)
    return attachment


async def download_avatar(user: discord.User) -> BytesIO:
    """Downloads a user's avatar."""
    attachment = BytesIO()
    await user.avatar_url.save(attachment)
    return attachment
