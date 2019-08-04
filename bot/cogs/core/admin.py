import inspect
import re

import discord
from discord.ext import commands

from bot.config import config as BOT_CONFIG
from bot.utils import checks


class Code:
    exec_test = re.compile(
        r"(?:^(?:(?:for)|(?:def)|(?:while)|(?:if)))|(?:^([a-z_][A-z0-9_\-\.]*)\s?(?:\+|-|\\|\*)?=)")

    @classmethod
    async def convert(cls, ctx: commands.Context, argument: str):

        lines = argument.split(';')
        result = []

        for line in lines:
            if cls.exec_test.match(line):
                result.append(
                    [line.strip(), cls.exec_test.match(line).group(1)])
            else:
                result.append([line.strip(), None])

        return result


class Admin(commands.Cog):
    """Bot management commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

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

    @commands.command(name='eval')
    async def eval(self, ctx: commands.Context, *, code: Code = []):
        """Evaluates python code.

        `code`: Python code to evaluate, new expressions are seperated with a `;`.
        """
        env = {
            'bot': self.bot,
            'ctx': ctx,
            'BOT_CONFIG': BOT_CONFIG
        }
        env.update(globals())

        results = []
        max_result_length = (
            2000 - (10 + sum(len(line) + 6 for line, is_exec in code))) // len(code)

        for line, is_exec in code:
            try:
                if is_exec is not None:
                    exec(line, env)
                    result = env.get(is_exec, None)
                    if inspect.isawaitable(result):
                        result = await result
                        env.update({is_exec: result})

                else:
                    result = eval(line, env)
                    if inspect.isawaitable(result):
                        result = await result

            except Exception as e:
                result = f"{type(e).__name__}: {e}"

            results.append([
                line,
                (str(result)[:max_result_length - 3] + "...") if len(str(result)) > max_result_length else str(result)])

        response_string = "```py\n" + \
            "\n".join([f">>> {line}\n{result}" for line, result in results]) + \
            "\n```"

        await ctx.send(response_string)


def setup(bot: commands.Bot):
    bot.add_cog(Admin(bot))
