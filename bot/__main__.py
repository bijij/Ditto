"""
Ditto Discord Bot

"""

import asyncio
import datetime
import logging
import traceback

import discord
from discord.ext import commands
from donphan import create_pool, create_tables, create_views

import bot.config as config
import bot.timers as timers

from bot.config import config as BOT_CONFIG

try:
    import uvloop
except ImportError:
    pass
else:
    uvloop.install()

_start_time = datetime.datetime.utcnow()

# Create bot instance
config._bot = timers._bot = bot = commands.Bot(
    command_prefix=commands.when_mentioned_or(*BOT_CONFIG.PREFIXES),
    activity=discord.Activity(
        name=f"for Commands: {BOT_CONFIG.PREFIXES[0]}help", type=discord.ActivityType.watching),
    case_insensitive=True
)

bot.__version__ = BOT_CONFIG.VERSION
bot._start_time = _start_time
bot.dm_help = False

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
async def on_command_error(ctx: commands.Context, error: Exception):
    # Ignore if CommandNotFound
    if isinstance(error, commands.CommandNotFound):
        return

    # Ignore if command has on error handler
    if hasattr(ctx.command, 'on_error'):
        return

    # Ignore if cog has a command error handler
    if ctx.cog is not None:
        if commands.Cog._get_overridden_method(ctx.cog.cog_command_error) is not None:
            return

    # Respond with error message if CheckFailure, CommandDisabled, CommandOnCooldown or UserInputError
    if isinstance(error, (commands.CheckFailure, commands.CommandOnCooldown, commands.UserInputError)):
        return await ctx.send(embed=discord.Embed(
            title=f'Error with command: {ctx.command.name}',
            description=str(error)
        ))

    # Otherwise log error
    bot.log.error(f'Error with command: {ctx.command.name}')
    bot.log.error(f'{type(error).__name__}: {error}')
    bot.log.error(
        "".join(traceback.format_exception(type(error), error, error.__traceback__)))

    embed = discord.Embed()

    # Send to user
    embed = discord.Embed(
        title=f'Error with command: {ctx.command.name}',
        description=f'```py\n{type(error).__name__}: {error}\n```'
    )
    await ctx.send(embed=embed)

    # Send to error log channel
    embed.add_field(
        name='Channel', value=f'<#{ctx.channel.id}> (#{ctx.channel.name})')
    embed.add_field(name='User', value=f'<@{ctx.author.id}> ({ctx.author})')
    await BOT_CONFIG.ERROR_LOG_CHANNEL.send(embed=embed)


if __name__ == "__main__":

    # Load help extension
    bot.load_extension('bot.help')

    # Load extensions from config
    for extension in BOT_CONFIG.EXTENSIONS:
        try:
            bot.load_extension(extension)
        except commands.ExtensionFailed as error:
            bot.log.error(f'Failed to load extension: {extension}')
            bot.log.error(f'\t{type(error).__name__}: {error}')
            bot.log.error(
                "".join(traceback.format_exception(type(error), error, error.__traceback__)))

    # setup database
    bot.log.info('Setting up Database...')
    run = asyncio.get_event_loop().run_until_complete
    run(create_pool(BOT_CONFIG.DONPHAN.DSN, server_settings={
        'application_name': BOT_CONFIG.DONPHAN.APPLICATION_NAME}
    ))
    run(create_tables(drop_if_exists=BOT_CONFIG.DONPHAN.DELETE_TABLES_ON_STARTUP))
    run(create_views(drop_if_exists=BOT_CONFIG.DONPHAN.DELETE_VIEWS_ON_STARTUP))

    # Start the timer task
    bot._active_timer = asyncio.Event(loop=bot.loop)
    bot._current_timer = None
    bot._timer_task = bot.loop.create_task(timers._dispatch_timers())

    bot.log.info('Logging in...')
    bot.run(BOT_CONFIG.TOKEN)
