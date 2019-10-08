import asyncio

from collections import Counter

# import discord
from discord.ext import commands, tasks

import asyncpg
from donphan import Column, SQLType, Table

from bot.utils import checks

from bot.config import config as BOT_CONFIG
COG_CONFIG = BOT_CONFIG.EXTENSIONS[__name__]


class _Commands(Table):
    id: SQLType.Serial = Column(primary_key=True, auto_increment=True)
    guild_id: SQLType.BigInt = Column(index=True)
    channel_id: SQLType.BigInt
    author_id: SQLType.BigInt = Column(index=True)
    used_at: SQLType.Timestamp = Column(index=True)
    prefix: str
    command: str = Column(index=True)
    failed: bool = Column(index=True)


class CommandStats(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._batch_lock = asyncio.Lock(loop=bot.loop)
        self._data_batch = []

        self.bulk_insert_loop.add_exception_type(
            asyncpg.PostgresConnectionError)
        self.bulk_insert_loop.start()

    @commands.command(name='commandstats', aliases=['command_stats'], hidden=True)
    @commands.check(checks.is_owner)
    async def commandstats(self, ctx: commands.Context, limit=20):
        """Retrieves basic information about command statistics."""

        delta = ctx.message.created_at - self.bot._start_time
        hours = delta.total_seconds() / 3600
        total = sum(self.bot.command_stats.values())
        cph = total / hours

        if limit > 0:
            common = self.bot.command_stats.most_common(limit)
        else:
            common = self.bot.command_stats.most_common()[limit:]

        width = len(max(self.bot.command_stats, key=len))
        output = '\n'.join(f'{k:<{width}}: {c}' for k, c in common)

        await ctx.send(f'{total} command invokes observed ({cph:.2f}/hour):\n```\n{output}\n```')

    async def bulk_insert(self):
        if self._data_batch:
            await _Commands.insert_many(list(_Commands._columns.values())[1:], self._data_batch)
            self._data_batch.clear()

    async def register_command(self, ctx):
        if ctx.command is None:
            return

        command_name = ctx.command.qualified_name
        self.bot.command_stats[command_name] += 1

        async with self._batch_lock:
            self._data_batch.append((ctx.guild.id if ctx.guild is not None else None, ctx.channel.id, ctx.author.id,
                                     ctx.message.created_at, ctx.prefix, command_name, ctx.command_failed))

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        await self.register_command(ctx)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        await self.register_command(ctx)

    @tasks.loop(seconds=30.0)
    async def bulk_insert_loop(self):
        async with self._batch_lock:
            await self.bulk_insert()


def setup(bot: commands.Bot):
    if not hasattr(bot, 'command_stats'):
        bot.command_stats = Counter()

    bot.add_cog(CommandStats(bot))
