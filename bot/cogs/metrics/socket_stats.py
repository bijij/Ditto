from collections import Counter

# import discord
from discord.ext import commands

from bot.config import config as BOT_CONFIG
COG_CONFIG = BOT_CONFIG.EXTENSIONS[__name__]


class SocketStats(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='socketstats', aliases=['socket_stats'], hidden=True)
    async def socketstats(self, ctx: commands.Context):
        """Retrieves basic information about socket statistics."""
        delta = ctx.message.created_at - self.bot._start_time
        minutes = delta.total_seconds() / 60
        total = sum(self.bot.socket_stats.values())
        cpm = total / minutes
        socket_stats = "\n".join(
            f"{name}: {count}" for name, count in self.bot.socket_stats.items())
        await ctx.send(f'{total} socket events observed ({cpm:.2f}/minute):\n```\n{socket_stats}\n```')

    @commands.Cog.listener()
    async def on_socket_response(self, msg):
        self.bot.socket_stats[msg.get('t')] += 1


def setup(bot: commands.Bot):
    if not hasattr(bot, 'socket_stats'):
        bot.socket_stats = Counter()

    bot.add_cog(SocketStats(bot))
