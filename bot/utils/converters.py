import json

import discord
from discord.ext import commands


class Guild(commands.IDConverter):

    async def convert(self, ctx: commands.Context, argument: str):
        bot = ctx.bot
        match = self._get_id_match(argument)

        if match is None:
            result = discord.utils.get(bot.guilds, name=argument)

        else:
            guild_id = int(match.group(1))
            result = bot.get_guild(guild_id)

        if not isinstance(result, discord.Guild):
            raise commands.BadArgument(f'Guild "{argument}" not found.')

        return result


class User(commands.IDConverter):

    async def convert(self, ctx: commands.Context, argument: str):
        try:
            instance = commands.converter.UserConverter()
            return await instance.convert(ctx, argument)
        except commands.BadArgument:

            bot = ctx.bot
            match = self._get_id_match(argument)

            if match is None:
                result = None
            else:
                try:
                    user_id = int(match.group(1))
                    result = await bot.fetch_user(user_id)
                except discord.NotFound:
                    result = None

            if not isinstance(result, discord.User):
                raise commands.BadArgument(f'User "{argument}" not found.')

            return result


class Embed(commands.Converter):

    async def convert(self, ctx: commands.Context, argument: str):
        try:
            if argument.startswith('```') and argument.endswith('```'):
                return discord.Embed.from_dict(json.loads('\n'.join(argument.split('\n')[1:-1])))
            return discord.Embed.from_dict(json.loads(argument))
        except Exception:
            raise commands.BadArgument(
                'Could not generate embed from supplied JSON.')
