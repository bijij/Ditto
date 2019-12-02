from asyncio import TimeoutError
from inspect import Parameter
from typing import Any

import discord
from discord.ext import commands

from .message import add_reactions

__all__ = [
    'confirm', 'prompt'
]


async def _prompt(to_delete, ctx, converter, timeout, max_tries, confirm_after, delete_after):

    def check(message: discord.Message):
        if message.author == ctx.author and message.channel == ctx.channel:
            return True
        return False

    for i in range(1, max_tries + 1):
        try:
            to_delete.append(await ctx.bot.wait_for('message', check=check, timeout=timeout))

            try:
                result = await ctx.command.do_conversion(ctx, converter, to_delete[-1].content, Parameter('prompt', Parameter.POSITIONAL_OR_KEYWORD))
                break
            except commands.UserInputError as error:
                to_delete.append(await ctx.bot.on_command_error(ctx, error))

        except TimeoutError:
            raise commands.BadArgument('You did not confirm in time.')

    else:
        raise commands.BadArgument('Maximum attempts exceeded.')

    if confirm_after:
        to_delete.append(await ctx.send(f'Just to confirm: {result}?'))

        if not (await confirm(ctx, to_delete[-1], timeout=timeout, delete_after=False)):
            to_delete.append(await ctx.send(to_delete[0].content, embed=to_delete[0].embeds[0] if to_delete[0].embeds else None))
            return await _prompt(to_delete, ctx, converter, timeout, max_tries - i, confirm_after, delete_after)

    return result


async def confirm(ctx: commands.Context, message: discord.Message, *, timeout=60, delete_after=True) -> bool:
    """Prompts the user for confirmation.

    Args:
        ctx (commands.Context): The command context to use.
        message (discord.Message): The message to add reactions to.

    Kwargs:
        timeout (float): How long in seconds to wait before timing out.
            Default is 60 seconds.
        delete_after (bool): Determines wether the confirm should be deleted afterwards.
            Defaults to True.

    """
    confirm = False
    reactions = ['\N{thumbs up sign}', '\N{thumbs down sign}']

    def check(payload):
        if payload.message_id == message.id and payload.user_id == ctx.author.id:
            if str(payload.emoji) in reactions:
                return True
        return False

    await add_reactions(message, reactions)

    try:
        payload = await ctx.bot.wait_for('raw_reaction_add', check=check, timeout=timeout)
        if str(payload.emoji) == '\N{thumbs up sign}':
            confirm = True

    finally:
        if delete_after:
            await message.delete()

        return confirm


async def prompt(ctx: commands.Context, message: discord.Message, converter: Any = str, *, timeout=60, max_tries=3, confirm_after=False, delete_after=True):
    """confirms the user for input.

    Args:
        ctx (commands.Context): The command context to use.
        message (discord.Message): The initial message to resend on retry.
        converter (Any): The type to convert user input to.
            Defaults to str

    Kwargs:
        timeout (float): How long in seconds to wait before timing out.
            Default is 60 seconds.
        max_tries (int): How many attempts a user can make before failing.
            Defaults to 3.
        confirm_after (bool): Determines wether the input should be confirmed before returning.
            Defaults to False.
        delete_after (bool): Determines wether the prompt should be deleted afterwards.
            Defaults to True.

    """
    to_delete = [message]
    async with ctx.typing():
        result = await _prompt(to_delete, ctx, converter, timeout, max_tries, confirm_after, delete_after)

    if delete_after and isinstance(ctx.channel, discord.TextChannel):
        try:
            await ctx.channel.delete_messages(to_delete)
        except (discord.Forbidden, discord.HTTPException):
            pass

    return result
