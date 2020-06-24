# Copyright (C) 2018 - 2020 MrYacha. All rights reserved. Source code available under the AGPL.
#
# This file is part of SophieBot.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from typing import Any


class FormatListText:
    __slots__ = ['data_dict', 'titles_bold']

    def __init__(self, data_dict: dict, titles_bold=True) -> None:
        self.data_dict = data_dict
        self.titles_bold = titles_bold

    def get_sub_title(self, sub_title) -> str:
        if self.titles_bold:
            text = f'<b>{sub_title}:</b> '
        else:
            text = f'{sub_title} '

        return text

    def build_data_text(self, data, text="", space='  ') -> str:
        for key, value in data.items():
            text += '\n'
            text += space
            text += self.get_sub_title(key)
            if isinstance(value, dict):
                text = self.build_data_text(value, text, space + space)
            else:
                text += str(value)
        return text

    @property
    def data(self) -> dict:
        """Returns data dict"""
        return self.data_dict

    @property
    def text(self) -> str:
        """Returns formatted text"""
        return self.build_data_text(self.data_dict)

    def __getitem__(self, key) -> Any:
        """Returns data from dict"""
        return self.data_dict[key]

    def __setitem__(self, key, value) -> None:
        """Sets a value to data"""
        self.data_dict[key] = value

    def __delitem__(self, key) -> None:
        """Deletes item"""
        del self.data_dict[key]
