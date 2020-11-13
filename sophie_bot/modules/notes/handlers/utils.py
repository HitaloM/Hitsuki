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

from contextlib import suppress
from datetime import datetime

from aiogram.utils.exceptions import MessageNotModified
from pymongo import ReplaceOne

from sophie_bot.services.mongo import db
from ...utils.language import get_string
from ...utils.notes import ALLOWED_COLUMNS
from ..utils.get import get_note


async def __stats__():
    text = "* <code>{}</code> total notes\n".format(
        await db.notes.count_documents({})
    )
    return text


async def __export__(chat_id):
    data = []
    notes = await db.notes.find({'chat_id': chat_id}).sort("names", 1).to_list(length=300)
    for note in notes:
        del note['_id']
        del note['chat_id']
        note['created_date'] = str(note['created_date'])
        if 'edited_date' in note:
            note['edited_date'] = str(note['edited_date'])
        data.append(note)

    return {'notes': data}


ALLOWED_COLUMNS_NOTES = ALLOWED_COLUMNS + [
    'names',
    'created_date',
    'created_user',
    'edited_date',
    'edited_user'
]


async def __import__(chat_id, data):
    if not data:
        return

    new = []
    for note in data:
        for item in [i for i in note if i not in ALLOWED_COLUMNS_NOTES]:
            del note[item]

        note['chat_id'] = chat_id
        note['created_date'] = datetime.fromisoformat(note['created_date'])
        if 'edited_date' in note:
            note['edited_date'] = datetime.fromisoformat(note['edited_date'])
        new.append(ReplaceOne({'chat_id': note['chat_id'], 'names': {'$in': [note['names'][0]]}}, note, upsert=True))

    await db.notes.bulk_write(new)


async def filter_handle(message, chat, data):
    chat_id = chat['chat_id']
    read_chat_id = message.chat.id
    note_name = data['note_name']
    note = await db.notes.find_one({'chat_id': chat_id, 'names': {'$in': [note_name]}})
    await get_note(message, db_item=note, chat_id=chat_id, send_id=read_chat_id, rpl_id=None)


async def setup_start(message):
    text = await get_string(message.chat.id, 'notes', 'filters_setup_start')
    with suppress(MessageNotModified):
        await message.edit_text(text)


async def setup_finish(message, data):
    note_name = message.text.split(' ', 1)[0].split()[0]

    if not (await db.notes.find_one({'chat_id': data['chat_id'], 'names': note_name})):
        await message.reply('no such note!')
        return

    return {'note_name': note_name}


__filters__ = {
    'get_note': {
        'title': {'module': 'notes', 'string': 'filters_title'},
        'handle': filter_handle,
        'setup': {
            'start': setup_start,
            'finish': setup_finish
        },
        'del_btn_name': lambda msg, data: f"Get note: {data['note_name']}"
    }
}
