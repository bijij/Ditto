
import copy
import io
import textwrap
import traceback

from contextlib import redirect_stdout
from typing import Union

import discord
from discord.ext import commands

from bot.config import config as BOT_CONFIG
from bot.utils import checks, converters


# Extra imports for eval
import asyncio
import datetime
import donphan
import inspect
import re


class Admin(commands.Cog):
    """Bot management commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._last_result = None  # For eval env

    async def cog_check(self, ctx: commands.Context) -> bool:
        return await checks.is_owner(ctx)

    @commands.command(name="sudo")
    async def sudo(self, ctx, user: Union[discord.Member, discord.User], *, command: str):
        """Run a command as another user."""
        msg = copy.copy(ctx.message)
        msg.author = user
        msg.content = ctx.prefix + command
        new_ctx = await self.bot.get_context(msg)
        try:
            await self.bot.invoke(new_ctx)
        except commands.CommandInvokeError as e:
            raise e.original

    @commands.command(name='eval')
    async def eval(self, ctx: commands.Context, *, body: converters.Code):
        """Evaluates python code.

        `code`: Python code to evaluate.
        """
        env = {
            'CONFIG': BOT_CONFIG,
            'bot': self.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            '_': self._last_result
        }

        env.update(globals())

        stdout = io.StringIO()

        try:
            exec(f'async def func():\n{textwrap.indent(body, "  ")}', env)
        except Exception as e:
            return await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception:
            value = stdout.getvalue()
            await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            value = stdout.getvalue()

            if ret is None:
                if value:
                    await ctx.send(f'```py\n{value}\n```')
            else:
                self._last_result = ret
                await ctx.send(f'```py\n{value}{ret}\n```')


def setup(bot: commands.Bot):
    bot.add_cog(Admin(bot))
