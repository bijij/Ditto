from discord.ext import commands


def is_administrator():
    return commands.check(commands.has_guild_permissions(administrator=True))
