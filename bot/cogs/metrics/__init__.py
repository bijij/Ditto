import datetime
import io

from typing import Union

import discord
from discord.ext import commands

from PIL import Image

from bot.utils.converters import Colour, Guild, User
from bot.utils.tools import format_dt


class Metrics(commands.Cog):
    """Retrieve information on specific things."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='server_info', aliases=['serverinfo'])
    async def server_info(self, ctx: commands.Context, *, guild: Guild = None):
        """Get information on a server.

        `guild`: The server to get information on by ID.
        """

        guild = guild or ctx.guild

        # If server was not specified
        if guild is None:
            raise commands.BadArgument('You must specify a server.')

        embed = discord.Embed().set_author(
            name=f'Information on {guild}:'
        ).set_thumbnail(
            url=guild.icon_url
        ).add_field(
            name='ID:', value=guild.id
        ).add_field(
            name='Voice Region:', value=guild.region
        ).add_field(
            name='Created At:', value=format_dt(guild.created_at)
        ).add_field(
            name='Owner:', value=guild.owner
        ).add_field(
            name='Member Count:', value=guild.member_count
        ).add_field(
            name='Channel Count:', value=len(guild.channels)
        ).add_field(
            name='Role Count:', value=len(guild.roles)
        ).add_field(
            name='Emoji Count:', value=len(guild.emojis)
        ).add_field(
            name='Nitro Booster Count:', value=guild.premium_subscription_count
        ).add_field(
            name='Features:', value=', '.join(guild.features) or 'None', inline=False
        )

        await ctx.send(embed=embed)

    @commands.command(name='role_info', aliases=['roleinfo'])
    async def role_info(self, ctx: commands.Context, *, role: discord.Role = None):
        """Get information on a role.

        `role`: The role to get information on by name, ID, or mention.
        """

        # If role was not specified
        if role is None:
            raise commands.BadArgument('You must specify a role.')

        embed = discord.Embed(
            colour=role.colour if role.colour.value else discord.Embed.Empty
        ).set_author(
            name=f'Information on {role}:'
        ).add_field(
            name='ID:', value=role.id
        ).add_field(
            name='Server:', value=role.guild
        ).add_field(
            name='Created At:', value=format_dt(role.created_at)
        ).add_field(
            name='Permissions:', value=f'[Permissions list](https://discordapi.com/permissions.html#{role.permissions.value})'
        ).add_field(
            name='Displayed Separately:', value='Yes' if role.hoist else 'No'
        ).add_field(
            name='Is Mentionable:', value='Yes' if role.mentionable else 'No'
        ).add_field(
            name='Colour:', value=role.colour if role.colour.value else 'None'
        )

        if len(role.members) <= 10:
            embed.add_field(
                name='Members:', value=', '.join(str(m) for m in role.members) or 'None', inline=False
            )
        else:
            embed.add_field(
                name='Member Count:', value=len(role.members)
            )

        await ctx.send(embed=embed)

    @commands.command(name='channel_info', aliases=['channelinfo'])
    async def channel_info(self, ctx: commands.Context, *, channel: Union[discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel] = None):
        """Get information on a channel.

        `channel[Optional]`: The channel to get information on by name, ID, or mention. If none specified it defaults to the channel you're in.
        """

        channel = channel or ctx.channel

        # If channel was not specified
        if isinstance(channel, discord.DMChannel):
            raise commands.BadArgument('You must specify a channel.')

        embed = discord.Embed().set_author(
            name=f'Information on {channel}:'
        ).add_field(
            name='ID:', value=channel.id
        ).add_field(
            name='Server:', value=channel.guild
        ).add_field(
            name='Created At:', value=format_dt(channel.created_at)
        )

        if isinstance(channel, discord.CategoryChannel):
            embed.add_field(
                name='Channel Count:', value=len(channel.channels)
            )
        else:
            embed.add_field(
                name='Category:', value=channel.category
            )

        if isinstance(channel, discord.TextChannel):
            embed.add_field(
                name='Channel Description:', value=channel.topic or 'None set.'
            ).add_field(
                name='Is NSFW:', value='Yes' if channel.is_nsfw() else 'No'
            ).add_field(
                name='Is News Channel:', value='Yes' if channel.is_news() else 'No'
            )

        elif isinstance(channel, discord.VoiceChannel):
            embed.add_field(
                name='Bitrate:', value=channel.bitrate
            ).add_field(
                name='User Limit:', value=channel.user_limit
            )

        await ctx.send(embed=embed)

    @commands.command(name='user_info', aliases=['userinfo'])
    async def user_info(self, ctx: commands.Context, *, user: Union[discord.Member, User] = None):
        """Get information on a user.

        `user[Optional]`: The user to get information on by name, ID, or mention. If none specified it defaults to you.
        """

        user = user or ctx.author

        embed = discord.Embed(
            colour=user.colour if user.colour.value else discord.Embed.Empty
        ).set_author(
            name=f'Information on {user}:'
        ).set_thumbnail(
            url=user.avatar_url
        ).add_field(
            name='ID:', value=user.id
        ).add_field(
            name='Account Created:', value=format_dt(user.created_at)
        )

        if isinstance(user, discord.Member):
            embed.add_field(
                name='Nickname:', value=user.nick
            ).add_field(
                name='Joined Server:', value=format_dt(user.joined_at)
            ).add_field(
                name='Nitro Boosting:', value=f'Since {format_dt(user.premium_since)}' if user.premium_since else 'No'
            )

            if len(user.roles[1:]) <= 10:
                embed.add_field(
                    name='Roles:', value=', '.join(str(m) for m in user.roles[1:]) or 'None', inline=False
                )
            else:
                embed.add_field(
                    name='Role Count:', value=len(user.roles[1:])
                )

        embed.add_field(
            name='Is Bot:', value='Yes' if user.bot else 'No'
        )

        await ctx.send(embed=embed)

    @commands.command(name='emoji_info', aliases=['emojiinfo'])
    async def emoji_info(self, ctx: commands.Context, *, emoji: Union[discord.Emoji, discord.PartialEmoji] = None):
        """Get information on an emoji.

        `emoji`: The emoji to get information on by name, ID or by the emoji itself.
        """

        # If emoji was not specified
        if emoji is None:
            raise commands.BadArgument('You must specify an emoji.')

        # If emoji is unicode emoji
        if isinstance(emoji, discord.PartialEmoji):
            if emoji.is_unicode_emoji():
                raise commands.BadArgument(
                    'Cannot retrieve information on Unicode emoji.')

        embed = discord.Embed().set_author(
            name=f'Information on {emoji.name}:'
        ).set_thumbnail(
            url=emoji.url
        ).add_field(
            name='ID:', value=emoji.id
        )

        if isinstance(emoji, discord.Emoji):
            embed.add_field(
                name='Server:', value=emoji.guild
            ).add_field(
                name='Uploaded At:', value=format_dt(emoji.created_at)
            )

        embed.add_field(
            name='Is animated:', value='Yes' if emoji.animated else 'No'
        )

        await ctx.send(embed=embed)

    @commands.command(name='invite_info', aliases=['inviteinfo'])
    async def invite_info(self, ctx: commands.Context, *, invite: discord.Invite = None):
        """Get information on a server invite.

        `invite`: The server invite to get information on, either by name, or the url.
        """

        # If invite was not specified
        if invite is None:
            raise commands.BadArgument('You must specify an invite url.')

        embed = discord.Embed().set_author(
            name=f'Information on invite to {invite.guild}:'
        ).set_thumbnail(
            url=invite.guild.icon_url
        ).add_field(
            name='Created At:', value=format_dt(invite.created_at) if invite.created_at else 'Unknown'
        ).add_field(
            name='Created By:', value=invite.inviter or 'Unknown'
        ).add_field(
            name='Expires:', value=format_dt(ctx.message.created_at + datetime.timedelta(seconds=invite.max_age)) if invite.max_age else 'Never'
        ).add_field(
            name='Channel:', value=invite.channel
        ).add_field(
            name='Uses:', value=invite.uses or 'Unknown'
        ).add_field(
            name='Max Uses:', value=invite.max_uses or 'Infinite'
        )

        await ctx.send(embed=embed)

    @commands.command(name='color_info', aliases=['colour_info', 'colorinfo', 'colourinfo'])
    async def colour_info(self, ctx: commands.Context, *, colour: Colour = None):
        """Get information on a colour.

        `colour:` The colour to get information on by hex or integer value.
        """

        # If colour was not specified
        if colour is None:
            raise commands.BadArgument('You must specify a colour.')

        embed = discord.Embed(
            colour=colour
        ).set_author(
            name=f'Information on: {colour}'
        ).add_field(
            name='Hex:', value=colour
        ).add_field(
            name='RGB:', value=', '.join(str(c) for c in colour.to_rgb())
        ).set_thumbnail(
            url=f'attachment://{colour.value:0>6x}.png'
        )

        with io.BytesIO() as fp_out:
            img = Image.new('RGB', (80, 80))
            img.paste(colour.to_rgb(), (0, 0, 80, 80))
            img.save(fp_out, 'PNG')
            fp_out.seek(0)

            await ctx.send(embed=embed, file=discord.File(fp_out, f'{colour.value:0>6x}.png'))

    @commands.command(name='get')
    async def get(self, ctx: commands.Context, *, item: Union[Guild, discord.Role, discord.TextChannel, discord.VoiceChannel,
                                                              discord.CategoryChannel, discord.Member, User, discord.Emoji,
                                                              discord.PartialEmoji, discord.Invite, Colour] = None):
        """Get information on something.

        `item`: The item to get information on; items are looked in the following order: Server, Role, Channel, User, Emoji, Invite, Colour.
        """

        if isinstance(item, discord.Guild):
            return await ctx.invoke(self.server_info, guild=item)

        if isinstance(item, discord.Role):
            return await ctx.invoke(self.role_info, role=item)

        if isinstance(item, (discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel)):
            return await ctx.invoke(self.channel_info, channel=item)

        if isinstance(item, (discord.User, discord.Member, discord.ClientUser)):
            return await ctx.invoke(self.user_info, user=item)

        if isinstance(item, (discord.Emoji, discord.PartialEmoji)):
            return await ctx.invoke(self.emoji_info, emoji=item)

        if isinstance(item, discord.Invite):
            return await ctx.invoke(self.invite_info, invite=item)

        if isinstance(item, discord.Colour):
            return await ctx.invoke(self.colour_info, colour=item)

        raise commands.BadArgument(
            f'Could not find information on item: {item}')


def setup(bot: commands.Bot):
    bot.add_cog(Metrics(bot))
