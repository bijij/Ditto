import discord
from discord.ext import commands, menus

from utils import EmbedPaginator


class EmbedHelpCommand(commands.DefaultHelpCommand):

    def __init__(self, **options):
        options.update({
            'paginator': EmbedPaginator(max_fields=8)
        })

        super().__init__(**options)

    async def send_pages(self):
        destination = self.get_destination()

        self.paginator.colour = self.context.me.colour
        self.paginator.set_author(
            name=f'{self.context.me} Help Manual',
            icon_url=self.context.me.avatar_url
        )
        self.paginator.set_footer(
            text=self.get_ending_note()
        )

        try:
            menu = menus.MenuPages(self.paginator, clear_reactions_after=True, check_embeds=True, delete_message_after=True)
            await menu.start(self.context, channel=destination)

        except menus.MenuError:
            raise commands.UserInputError('I was not able to send command help.')

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
