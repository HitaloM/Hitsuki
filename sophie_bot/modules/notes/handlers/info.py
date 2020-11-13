# Copyright (C) 2018 - 2020 MrYacha. All rights reserved. Source code available under the AGPL.
# Copyright (C) 2019 Aiogram
# Copyright (C) 2020 Jeepeo

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

from babel.dates import format_datetime

from sophie_bot.decorator import register
from sophie_bot.services.mongo import db
from ..utils.clean_notes import clean_notes
from ..utils.get import get_similar_note
from ...utils.connections import chat_connection
from ...utils.language import get_strings_dec
from ...utils.message import get_arg, need_args_dec
from ...utils.text import *
from ...utils.user_details import get_user_link


@register(cmds='noteinfo', user_admin=True)
@chat_connection()
@need_args_dec()
@get_strings_dec('notes')
@clean_notes
async def note_info(message, chat, strings):
    note_name = get_arg(message).lower()
    if note_name[0] == '#':
        note_name = note_name[1:]

    if not (note := await db.notes.find_one({'chat_id': chat['chat_id'], 'names': {'$in': [note_name]}})):
        text = strings['cant_find_note'].format(chat_name=chat['chat_title'])
        if alleged_note_name := await get_similar_note(chat['chat_id'], note_name):
            text += strings['u_mean'].format(note_name=alleged_note_name)
        return await message.reply(text)

    sec = Section(title=strings['note_info_title'])

    note_names = ''
    for note_name in note['names']:
        note_names += f" <code>#{note_name}</code>"

    sec += KeyValue(strings['note_info_note'], note_names)
    sec += KeyValue(strings['note_info_content'], ('text' if 'file' not in note else note['file']['type']))

    if 'parse_mode' not in note or note['parse_mode'] == 'md':
        parse_mode = 'Markdown'
    elif note['parse_mode'] == 'html':
        parse_mode = 'HTML'
    elif note['parse_mode'] == 'none':
        parse_mode = 'None'
    else:
        raise NotImplemented()

    if 'group' in note:
        sec += KeyValue(strings['note_info_group'], Code(f"#{note['group']}"))

    sec += KeyValue(strings['note_info_parsing'], Code(parse_mode))

    if 'created_date' in note:
        sec += strings['note_info_created'].format(
            date=format_datetime(note['created_date'], locale=strings['language_info']['babel']),
            user=await get_user_link(note['created_user'])
        )

    if 'edited_date' in note:
        sec += strings['note_info_updated'].format(
            date=format_datetime(note['edited_date'], locale=strings['language_info']['babel']),
            user=await get_user_link(note['edited_user'])
        )

    return await message.reply(str(sec))
