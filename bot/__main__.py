import asyncio
import datetime
import logging

import discord
from discord.ext import commands

import bot.config
from bot.config import config as BOT_CONFIG
from bot.utils import Bot

from donphan import create_pool, create_tables

try:
    import uvloop
except ImportError:
    pass
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

_start_time = datetime.datetime.utcnow()

# Create bot instance
bot.config._bot = bot = Bot(
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
        bot.load_extension(extension)

    # setup database
    run = asyncio.get_event_loop().run_until_complete
    run(create_pool(BOT_CONFIG.DONPHAN_DSN))
    run(create_tables(drop_if_exists=BOT_CONFIG.DELETE_TABLES_ON_STARTUP))

    bot.run(BOT_CONFIG.TOKEN)
