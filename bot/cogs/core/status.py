import asyncio

import discord
from discord.ext import commands

from bot.config import config as BOT_CONFIG
from bot.utils import checks


class Status(commands.Cog):
    """Bot information commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='ping')
    @commands.check(checks.is_owner)
    async def ping(self, ctx: commands.Context):
        """Determines the bots current latency"""
        message = await ctx.send('Pong!')
        await message.edit(content=f'Pong! Latency: `{(message.created_at - ctx.message.created_at).total_seconds()}s`')

    @commands.command(name='status')
    @commands.check(checks.is_owner)
    async def status(self, ctx: commands.Context):
        """Shows some basic information about the bot's current status."""
        await ctx.send(
            embed=discord.Embed(
                title=f'{self.bot.user.name} v{self.bot.__version__} Status:',
                colour=self.bot.user.colour
            ).set_thumbnail(
                url=self.bot.user.avatar_url
            ).add_field(
                name="Users:", value=len(self.bot.users)
            ).add_field(
                name="Guilds:", value=len(self.bot.guilds)
            ).add_field(
                name="Started at:", value=self.bot._start_time.strftime('%F %H:%M:%S UTC')
            ).add_field(
                name="Cogs loaded:", value=len(self.bot.cogs)
            )
        )


def setup(bot: commands.Bot):
    bot.add_cog(Status(bot))
