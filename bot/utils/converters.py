import colorsys
import json
import re

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


class Code(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str):
        if argument.startswith('```') and argument.endswith('```'):
            return '\n'.join(argument.split('\n')[1:-1])
        return argument.strip('` \n')


class Colour(commands.ColourConverter):
    async def convert(self, ctx: commands.Context, argument: str):
        try:
            return await super().convert(ctx, argument)
        except commands.BadArgument as e:
            # rgb()
            match = re.match(r'rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', argument, re.IGNORECASE)
            if match is not None:
                r, g, b = (int(x) for x in match.groups())
                return discord.Colour.from_rgb(r, g, b)

            # hsl()
            match = re.match(r'hsl\(\s*(\d+)\s*,\s*(\d+(?:\.\d+)?)\%\s*,\s*(\d+(?:\.\d+)?)\%\s*\)', argument, re.IGNORECASE)
            if match is not None:
                rgb = colorsys.hls_to_rgb(int(match.group(1)) / 360, *(float(x) / 100 for x in match.groups()[-1:0:-1]))
                return discord.Colour.from_rgb(*(int(x * 255) for x in rgb))

            raise e


Color = Colour


class Embed(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str):
        try:
            code = await Code().convert(ctx, argument)
            return discord.Embed.from_dict(json.loads(code))
        except Exception:
            raise commands.BadArgument(
                'Could not generate embed from supplied JSON.')
