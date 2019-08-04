import asyncio
import datetime
import logging

import discord
from discord.ext import commands

import bot.config as config
import bot.timers as timers

from donphan import create_pool, create_tables

from bot.config import config as BOT_CONFIG

try:
    import uvloop
except ImportError:
    pass
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

_start_time = datetime.datetime.utcnow()

# Create bot instance
config._bot = timers._bot = bot = commands.Bot(
    command_prefix=commands.when_mentioned_or(*BOT_CONFIG.PREFIXES)
)

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


if __name__ == '__main__':

    # Load extensions from config
    for extension in BOT_CONFIG.EXTENSIONS:
        try:
            bot.load_extension(extension)
        except Exception as e:
            bot.log.error(f'Failed to load extension: {extension}')
            bot.log.error(f'\t{type(e).__name__}: {e}')

    # setup database
    run = asyncio.get_event_loop().run_until_complete
    run(create_pool(BOT_CONFIG.DONPHAN_DSN))
    run(create_tables(drop_if_exists=BOT_CONFIG.DELETE_TABLES_ON_STARTUP))

    # Start the timer task
    bot._active_timer = asyncio.Event(loop=bot.loop)
    bot._current_timer = None
    bot._timer_task = bot.loop.create_task(timers._dispatch_timers())

    bot.run(BOT_CONFIG.TOKEN)
