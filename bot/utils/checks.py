import discord
from discord.ext import commands


async def is_owner(ctx: commands.Context):
    return await ctx.bot.is_owner(ctx.author)
