import asyncio

import discord
from discord.ext import commands

from bot.utils import checks

from bot.config import config as BOT_CONFIG


class Git(commands.Cog):
    """Bot management commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_check(self, ctx: commands.Context) -> bool:
        return await checks.is_owner(ctx)

    @commands.command(name='load', hidden=True)
    async def load(self, ctx: commands.Context, cog: str):
        """Loads a cog.

        `cog`: The cog to load.
        """
        cog = f'bot.cogs.{cog}'

        self.bot.load_extension(cog)
        await ctx.send(embed=discord.Embed(
            title=f'Successfully loaded extension: {cog}',
            colour=0xf44336
        ))

    @commands.command(name='unload', hidden=True)
    async def unload(self, ctx: commands.Context, cog: str):
        """Unloads a cog.

        `cog`: The cog to unload.
        """
        cog = f'bot.cogs.{cog}'

        self.bot.unload_extension(cog)
        await ctx.send(embed=discord.Embed(
            title=f'Successfully unloaded extension: {cog}',
            colour=0xf44336
        ))

    @commands.command(name='reload', hidden=True)
    async def reload(self, ctx: commands.Context, cog: str):
        """Reloads a cog.

        `cog`: The cog to reload.
        """
        cog = f'bot.cogs.{cog}'

        self.bot.reload_extension(cog)
        await ctx.send(embed=discord.Embed(
            title=f'Successfully reloaded extension: {cog}',
            colour=0xf44336
        ))

    @commands.command(name='reload_config')
    async def reload_config(self, ctx: commands.Context):
        """Reload the bot's config."""
        BOT_CONFIG.__reload__()
        await ctx.send('Config Reloaded.')

    @commands.command(name='pull', hidden=True)
    async def pull(self, ctx: commands.Context):
        """Pulls the most recent version of the repository."""

        p = await asyncio.create_subprocess_exec(
            'git', 'pull',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await p.communicate()

        err = stderr.decode()
        if not err.startswith('From'):
            raise commands.CommandError(f'Failed to pull!\n\n{err}')

        resp = stdout.decode()

        if len(resp) > 1024:
            resp = resp[:1020] + '...'

        embed = discord.Embed(
            title='Git pull...',
            description=f'```diff\n{resp}\n```',
            colour=0x009688,
        )

        await ctx.send(embed=embed)

        if 'Pipfile.lock' in resp:
            raise commands.BadArgument(
                '**Pipfile.lock was modified!**\nPlease ensure you install the latest packages before restarting.')

        elif 'config.yml' in resp:
            raise commands.BadArgument(
                '**config.yml was modified!**\nPlease ensure you reload the config using either `!reload_config` or by restarting.')

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
