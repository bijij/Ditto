import asyncio

import discord
from discord.ext import commands

from bot.config import config as BOT_CONFIG
from bot.utils import Bot, Context


class Git(commands.Cog):
    """Bot management commands."""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def cog_check(self, ctx: Context) -> bool:
        return self.bot.is_owner(ctx.author)

    @commands.command(name="pull", hidden=True)
    async def pull(self, ctx: Context):
        """Pulls the most recent version of the repository."""
        p = await asyncio.create_subprocess_exec(
            'git', 'pull',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await p.communicate()

        err = stderr.decode()
        if not err.startswith("From"):
            raise commands.CommandError(f"Failed to pull!\n\n{err}")

        resp = stdout.decode()
        if len(resp) > 1024:
            resp = resp[:1020] + '...'

        embed = discord.Embed(
            title="Git pull...",
            description=f"```diff\n{resp}\n```",
            colour=0x009688,
        )

        if 'Pipfile.lock' in resp:
            embed.add_field(
                name="Pipflie.lock was modified!",
                value='Please ensure you install the latest packages before restarting.'
            )

        await ctx.send(embed=embed)

    @commands.command(name='restart')
    async def restart(self, ctx: Context, arg: str = None):
        """Restarts the bot."""
        if arg == 'pull':
            await ctx.invoke(self.pull)

        await ctx.send(embed=discord.Embed(
            title='Restarting...',
            colour=discord.Colour.red()
        ))

        self.bot.log.info(f'Restarting')
        await self.bot.logout()


def setup(bot: Bot):
    bot.add_cog(Git(bot))
