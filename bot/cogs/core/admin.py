import copy
import inspect
import io
import re
import textwrap
import traceback

from contextlib import redirect_stdout
from typing import Union

import discord
from discord.ext import commands

from bot.config import config as BOT_CONFIG
from bot.utils import checks


# Extra imports for eval
import datetime

import donphan


class Code:

    @classmethod
    async def convert(cls, ctx: commands.Context, argument: str):
        if argument.startswith('```') and argument.endswith('```'):
            return '\n'.join(argument.split('\n')[1:-1])
        return argument.strip('` \n')


class Admin(commands.Cog):
    """Bot management commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._last_result = None  # For eval env

    async def cog_check(self, ctx: commands.Context) -> bool:
        return await checks.is_owner(ctx)

    @commands.command(name='load')
    async def load(self, ctx: commands.Context, extension: str):
        """Loads an extension."""
        self.bot.log.info(f'Loading extension: {extension}')
        self.bot.load_extension(extension)
        await ctx.send(embed=discord.Embed(
            title=f'Succesfully loaded extension: {extension}.'
        ))

    @commands.command(name='unload')
    async def unload(self, ctx: commands.Context, extension: str):
        """Loads an extension."""
        self.bot.log.info(f'Unloading extension: {extension}')
        self.bot.unload_extension(extension)
        await ctx.send(embed=discord.Embed(
            title=f'Succesfully unloaded extension: {extension}.'
        ))

    @commands.command(name='reload')
    async def reload(self, ctx: commands.Context, extension: str):
        """Loads an extension."""
        self.bot.log.info(f'Reloading extension: {extension}')
        self.bot.reload_extension(extension)
        await ctx.send(embed=discord.Embed(
            title=f'Succesfully reloaded extension: {extension}.'
        ))

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
    async def eval(self, ctx: commands.Context, *, body: Code):
        """Evaluates python code.

        `code`: Python code to evaluate, new expressions are seperated with a `;`.
        """
        env = {
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
        except Exception as e:
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
