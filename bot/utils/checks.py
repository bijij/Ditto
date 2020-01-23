from typing import Union, Callable

import discord
from discord.ext import commands


def any_check(ctx: Union[discord.Message, commands.Context], *checks: Callable) -> bool:
    """Returns :True: when any provided check has passed."""
    for check in checks:
        try:
            return check(ctx)
        except commands.CheckFailure:
            continue
    return False


async def is_owner(ctx: commands.Context):
    return await ctx.bot.is_owner(ctx.author)


def is_guild(ctx: Union[discord.Message, commands.Context]) -> bool:
    if ctx.guild is None:
        raise commands.NoPrivateMessage(
            'You must use this command in a server.')
    return True


def is_direct_message(ctx: commands.Context) -> bool:
    if not isinstance(ctx.channel, discord.DMChannel):
        raise commands.PrivateMessageOnly(
            'You must use this command in a direct message.')
    return True


def has_administrator_permission(ctx: commands.Context) -> bool:
    is_guild(ctx)
    commands.has_permissions(administrator=True)(ctx)
    commands.bot_has_permissions(administrator=True)(ctx)
    return True
