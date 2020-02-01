# Copyright (C) 2019 The Raphielscape Company LLC.
# Copyright (C) 2018-2019 MrYacha
# Copyright (C) 2017-2019 Aiogram
#
# This file is part of SophieBot.
#
# SophieBot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.


def tbold(text, sep=' '):
    return f'**{text}**'


def titalic(text, sep=' '):
    return f'__{text}__'


def tcode(text, sep=' '):
    return f'`{text}`'


def tpre(text, sep=' '):
    # TODO: pass
    return f'[{text}['


def tstrikethrough(text, sep=' '):
    return f'~~{text}~~'


def tunderline(text, sep=' '):
    # Telethon's markdown parser not supporting underline currently
    return f'{text}'


def tlink(title, url):
    return "[{0}]({1})".format(title, url)
