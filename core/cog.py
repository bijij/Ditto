import discord
from discord.ext import commands

from .config import Config


class Cog(commands.Cog):

    def __init__(self, bot: commands.Bot, config: Config):
        self.bot = bot
        self.config = config
