import asyncio

import discord
from discord.ext import commands


class Context(commands.Context):

    async def previous_message(self) -> discord.Message:
        """Retrives the message sent befoire command invoke.
        """
        async for message in self.channel.history(limit=2):
            pass
        return message

    async def prompt(self, message: str, *, timeout=60, delete_after=True) -> bool:
        """Prompts the user for confirmation.

        Args:
            message (str): The message to send with the prompt.

        Kwargs:
            timeout (float): How long in seconts to wait before timing out.
                Default is 60 seconds.
            delete_after (bool): Determines wether the prompt should be deleted afterwards.
                Defaults to True.

        """
        message = await self.send(message)
        confirm = False

        def check(payload):
            if payload.message_id == message.id and payload.user_id == self.author.id:
                if str(payload.emoji) in ['👍', '👎']:
                    return True
            return False

        for emoji in ['👍', '👎']:
            await message.add_reaction(emoji)

        try:
            payload = await self.bot.wait_for('raw_reaction_add', check=check, timeout=timeout)
            if str(payload.emoji) == '👍':
                confirm = True

        finally:
            if delete_after:
                await message.delete()

            return confirm
