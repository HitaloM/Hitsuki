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

from sophie_bot import bot
from sophie_bot.services.mongo import db
from ...utils.language import get_strings_dec
from ...utils.notes import t_unparse_note_item, send_note

from ...utils.text import *


async def get_similar_note(chat_id, note_name):
    all_notes = []
    async for note in db.notes.find({'chat_id': chat_id}):
        all_notes.extend(note['names'])

    if len(all_notes) > 0:
        check = difflib.get_close_matches(note_name, all_notes)
        if len(check) > 0:
            return check[0]

    return None


@get_strings_dec('notes')
async def get_note(message, strings, note_name=None, db_item=None,
                   chat_id=None, send_id=None, rpl_id=None, noformat=False, event=None, user=None):
    if not chat_id:
        chat_id = message.chat.id

    if not send_id:
        send_id = message.chat.id

    if rpl_id is False:
        rpl_id = None
    elif not rpl_id:
        rpl_id = message.message_id

    if not db_item and not (db_item := await db.notes.find_one({'chat_id': chat_id, 'names': {'$in': [note_name]}})):
        await bot.send_message(
            chat_id,
            strings['no_note'],
            reply_to_message_id=rpl_id
        )
        return

    text, kwargs = await t_unparse_note_item(message, db_item, chat_id, noformat=noformat, event=event, user=user)
    kwargs['reply_to'] = rpl_id

    return await send_note(send_id, text, **kwargs)


@get_strings_dec('notes')
async def get_notes_list(message, chat, strings, keyword=None):
    if not (notes := await db.notes.find({'chat_id': chat['chat_id']}).sort("names", 1).to_list(length=300)):
        return await message.reply(strings["notelist_no_notes"].format(chat_title=chat['chat_title']))

    doc = SanTeXDoc()
    notes_section = Section(title=strings['notelist_header'].format(chat_name=chat['chat_title']))

    # Search
    pattern = keyword or message.get_args()
    if pattern and len(pattern) > 0:
        notes_section += KeyValue(strings['search_pattern'], Code(pattern))

        all_notes = notes
        notes = []
        for note in all_notes:
            for note_name in note['names']:
                if pattern in note_name:
                    notes.append(note)
                    break

    notes_list = []
    for note in notes:
        note_names = ''
        for note_name in note['names']:
            note_names += f'<code>#{note_name}</code> '

        notes_list.append(note_names)

    notes_section += SList(*notes_list)
    doc += notes_section
    doc += strings['you_can_get_note'].format(note_name='notename')

    return await message.reply(str(doc))
