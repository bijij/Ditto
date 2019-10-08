import discord
from discord.ext import commands

from bot.utils.paginator import EmbedPaginator


class EmbedHelpCommand(commands.DefaultHelpCommand):

    def __init__(self, **options):
        super().__init__(**options, paginator=options.pop('paginator', EmbedPaginator()))

    def get_ending_note(self):
        return None

    async def send_pages(self):
        destination = self.get_destination()

        try:
            for i, page in enumerate(self.paginator.pages):
                page.set_author(
                    name=f'{self.context.me} Help Manual{" Cont." if i > 0 else ""}:',
                    icon_url=self.context.me.avatar_url
                )
                page.set_footer(
                    text=super().get_ending_note()
                )
                page.colour = self.context.me.colour

                await destination.send(embed=page)
        except discord.Forbidden:
            await self.context.send(
                embed=discord.Embed(
                    title='Error with command: help',
                    description='I was not able to Direct Message you.\nDo you have direct messages disabled?'
                )
            )

    def get_command_signature(self, command):
        return f'Syntax: `{super().get_command_signature(command)}`'

    def add_indented_commands(self, commands, *, heading, max_size=None):
        if not commands:
            return

        max_size = max_size or self.get_max_size(commands)

        lines = []
        get_width = discord.utils._string_width
        for command in commands:
            name = command.name
            width = max_size - (get_width(name) - len(name))
            entry = '{0}**{1:<{width}}**: {2}'.format(
                self.indent * ' ', name, command.short_doc, width=width)
            lines.append(self.shorten_text(entry))

        self.paginator.add_field(
            name=heading,
            value='\n'.join(lines)
        )
