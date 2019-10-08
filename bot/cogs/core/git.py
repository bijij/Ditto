import asyncio

import discord
from discord.ext import commands

from bot.utils import checks


class Git(commands.Cog):
    """Bot management commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_check(self, ctx: commands.Context) -> bool:
        return await checks.is_owner(ctx)

    @commands.command(name="pull")
    async def pull(self, ctx: commands.Context):
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
    async def restart(self, ctx: commands.Context, arg: str = None):
        """Restarts the bot."""
        if arg == 'pull':
            await ctx.invoke(self.pull)

        await ctx.send(embed=discord.Embed(
            title='Restarting...',
            colour=discord.Colour.red()
        ))

        self.bot.log.info(f'Restarting')
        await self.bot.logout()


def setup(bot: commands.Bot):
    bot.add_cog(Git(bot))
