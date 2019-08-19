import discord
from discord.ext import commands


class EmbedPaginator(commands.Paginator):

    def __init__(self):
        self.clear()
        self._count = 0

    def clear(self):
        self._current_page = discord.Embed(description='')
        self._pages = []

    def add_line(self, line='', *, empty=False):
        max_description_size = 2048
        if len(line) > max_description_size:
            raise RuntimeError('Line exceeds maximum size')

        # Close page if too large to add
        if len(self._current_page.description) + len(line) + 1 > max_description_size:
            self.close_page()

        max_embed_size = 5500
        if len(self._current_page) + len(line) + 1 > max_embed_size:
            self.close_page()

        self._current_page.description += '\n' + line + ('\n' if empty else '')

    def add_field(self, name, value, *, inline=False):

        max_field_name_size = 256
        if len(name) > max_field_name_size:
            raise RuntimeError('Field name exceeds maximum size')

        max_field_value_size = 1024
        if len(value) > max_field_value_size:
            raise RuntimeError('Field value exceeds maximum size')

        max_fields = 25
        if len(self._current_page.fields) == max_fields:
            self.close_page()

        max_embed_size = 5500
        if len(self._current_page) + len(name) + len(value) > max_embed_size:
            self.close_page()

        self._current_page.add_field(name=name, value=value, inline=inline)

    def close_page(self):
        self._pages.append(self._current_page)
        self._current_page = discord.Embed(description='')

    def __repr__(self):
        fmt = '<EmbedPaginator>'
        return fmt.format(self)


class EmbedHelpCommand(commands.DefaultHelpCommand):

    def __init__(self, **options):
        super().__init__(**options, paginator=options.pop('paginator', EmbedPaginator()))

    def get_ending_note(self):
        return None

    async def send_pages(self):
        destination = self.get_destination()

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
