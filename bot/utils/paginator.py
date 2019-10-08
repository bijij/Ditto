import discord
from discord.ext import commands


class EmbedPaginator(commands.Paginator):

    def __init__(self, embed=None):

        self._embed = embed or discord.Embed()

        self.clear()
        self._count = 0

    def new_page(self):
        self._current_page = self._embed.copy()
        self._current_page.description = ''

    def clear(self):
        self._pages = []
        self.new_page()

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

        # Add cont if required.
        if len(self._pages) >= 1:
            if self._current_page.author.name:
                self._current_page.set_author(
                    name=self._current_page.author.name + ' Cont.',
                    url=self._current_page.author.url,
                    icon_url=self._current_page.author.icon_url
                )

        self._pages.append(self._current_page)
        self.new_page()

    def __repr__(self):
        fmt = '<EmbedPaginator>'
        return fmt.format(self)
