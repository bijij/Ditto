import asyncio
import datetime
import inspect
import logging
import traceback

import discord
from discord.ext import commands

import bot.config as config

from bot.help import EmbedHelpCommand

from bot.config import config as BOT_CONFIG

try:
    import uvloop
except ImportError:
    pass
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

_start_time = datetime.datetime.utcnow()

# Create bot instance
config._bot = bot = commands.Bot(
    command_prefix=commands.when_mentioned_or(*BOT_CONFIG.PREFIXES),
    activity=discord.Activity(
        name=f"for Commands: {BOT_CONFIG.PREFIXES[0]}help", type=discord.ActivityType.watching),
    case_insensitive=True,
    help_command=EmbedHelpCommand(dm_help=None, dm_help_threshold=500),
)

bot.__version__ = BOT_CONFIG.VERSION
bot._start_time = _start_time

# Setup logging
bot.log = logging.getLogger(__name__)
bot.log.setLevel(logging.getLevelName(BOT_CONFIG.LOGGING_LEVEL))

handler = logging.FileHandler(filename=f'{BOT_CONFIG.APP_NAME}.log')
handler.setFormatter(logging.Formatter(
    '{asctime} - {levelname} - {message}', style='{'))

bot.log.addHandler(handler)
bot.log.addHandler(logging.StreamHandler())

bot.log.info('Instance starting...')


@bot.event
async def on_ready():
    bot.log.info(f'Succesfylly loggged in as {bot.user}...')
    bot.log.info(f'\tGuilds: {len(bot.guilds)}')
    bot.log.info(f'\tTook: {datetime.datetime.utcnow() - _start_time}')


@bot.event
async def on_command_error(ctx: commands.Context, e: Exception):
    # Ignore if CommandNotFound
    if isinstance(e, commands.CommandNotFound):
        return

    # Ignore if command has on error handler
    if hasattr(ctx.command, 'on_error'):
        return

    # Ignore if cog has a command error handler
    if ctx.cog is not None:
        if commands.Cog._get_overridden_method(ctx.cog.cog_command_error) is not None:
            return

    # Respond with error message if CheckFailure, CommandDisabled, CommandOnCooldown or UserInputError
    if isinstance(e, (commands.CheckFailure, commands.CommandOnCooldown, commands.UserInputError)):
        return await ctx.send(embed=discord.Embed(
            title=f'Error with command: {ctx.command.name}',
            description=str(e)
        ))

    # Otherwise log error
    bot.log.error(f'Error with command: {ctx.command.name}')
    bot.log.error(f'{type(e).__name__}: {e}')
    bot.log.error(
        "".join(traceback.format_exception(type(e), e, e.__traceback__)))

    embed = discord.Embed()

    # Send to user
    embed = discord.Embed(
        title=f'Error with command: {ctx.command.name}',
        description=f'```py\n{type(e).__name__}: {e}\n```'
    )
    await ctx.send(embed=embed)

    # Send to error log channel
    embed.add_field(
        name='Channel', value=f'<#{ctx.channel.id}> (#{ctx.channel.name})')
    embed.add_field(name='User', value=f'<@{ctx.author.id}> ({ctx.author})')
    await BOT_CONFIG.ERROR_LOG_CHANNEL.send(embed=embed)


if __name__ == "__main__":

    # Load extensions from config
    for extension in BOT_CONFIG.EXTENSIONS:
        try:
            bot.load_extension(extension)
        except Exception as e:
            bot.log.error(f'Failed to load extension: {extension}')
            bot.log.error(f'\t{type(e).__name__}: {e}')
            bot.log.error(
                "".join(traceback.format_exception(type(e), e, e.__traceback__)))

    bot.run(BOT_CONFIG.TOKEN)
