import discord
from discord.ext import commands

from bot.config import config as BOT_CONFIG


async def is_owner(ctx: commands.Context):
    return await ctx.bot.is_owner(ctx.author)
