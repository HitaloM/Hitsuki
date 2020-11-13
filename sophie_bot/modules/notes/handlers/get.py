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

import re

from aiogram.dispatcher.filters.builtin import CommandStart
from aiogram.types.inline_keyboard import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.deep_linking import get_start_link

from sophie_bot.decorator import register
from sophie_bot.services.mongo import db
from ..utils.clean_notes import clean_notes
from ..utils.get import get_note, get_notes_list, get_similar_note
from ...utils.connections import chat_connection, set_connected_command
from ...utils.disable import disableable_dec
from ...utils.language import get_strings_dec
from ...utils.message import get_arg, need_args_dec
from ...utils.text import *

RESTRICTED_SYMBOLS_IN_NOTENAMES = [':', '**', '__', '`', '"', '[', ']', "'", '$', '||', '^']


@register(cmds='get')
@disableable_dec('get')
@need_args_dec()
@chat_connection(command='get')
@get_strings_dec('notes')
@clean_notes
async def get_note_cmd(message, chat, strings):
    chat_id = chat['chat_id']
    chat_name = chat['chat_title']

    note_name = get_arg(message).lower()
    if note_name[0] == '#':
        note_name = note_name[1:]

    if 'reply_to_message' in message:
        rpl_id = message.reply_to_message.message_id
        user = message.reply_to_message.from_user
    else:
        rpl_id = message.message_id
        user = message.from_user

    if not (note := await db.notes.find_one({'chat_id': int(chat_id), 'names': {'$in': [note_name]}})):
        text = strings['cant_find_note'].format(chat_name=chat_name)
        if alleged_note_name := await get_similar_note(chat_id, note_name):
            text += strings['u_mean'].format(note_name=alleged_note_name)
        await message.reply(text)
        return

    noformat = False
    if len(args := message.text.split(' ')) > 2:
        arg2 = args[2].lower()
        noformat = arg2 in ('noformat', 'raw')

    return await get_note(
        message,
        db_item=note,
        rpl_id=rpl_id,
        noformat=noformat,
        user=user
    )


@register(regexp=r'^#([\w-]+)')
@disableable_dec('get')
@chat_connection(command='get')
@clean_notes
async def get_note_hashtag(message, chat, regexp=None):
    chat_id = chat['chat_id']
    note_name = message.text.split(' ', 1)[0][1:].lower()

    if not (note := await db.notes.find_one({'chat_id': int(chat_id), 'names': {'$in': [note_name]}})):
        return

    if 'reply_to_message' in message:
        rpl_id = message.reply_to_message.message_id
        user = message.reply_to_message.from_user
    else:
        rpl_id = message.message_id
        user = message.from_user

    return await get_note(
        message,
        db_item=note,
        rpl_id=rpl_id,
        user=user
    )


@register(cmds=['notes', 'saved', 'notelist', 'noteslist'])
@disableable_dec('notes')
@chat_connection(command='notes')
@get_strings_dec('notes')
@clean_notes
async def get_notes_list_cmd(message, chat, strings):
    if await db.privatenotes.find_one({'chat_id': chat['chat_id']}) \
            and message.chat.id == chat['chat_id']:  # Workaround to avoid sending PN to connected PM
        text = strings['notes_in_private']
        if not (keyword := message.get_args()):
            keyword = None
        button = InlineKeyboardMarkup().add(InlineKeyboardButton(
            text='Click here',
            url=await get_start_link(f"notes_{chat['chat_id']}_{keyword}")
        ))
        return await message.reply(text, reply_markup=button, disable_web_page_preview=True)
    else:
        return await get_notes_list(message, chat)


@register(cmds='search')
@chat_connection()
@get_strings_dec('notes')
@clean_notes
async def search_in_note(message, chat, strings):
    pattern = message.get_args()
    doc = SanTeXDoc()
    sec = Section(
        KeyValue(strings['search_pattern'], Code(pattern)),
        title=strings["search_header"].format(chat_name=chat['chat_title'])
    )

    notes = db.notes.find({
        'chat_id': chat['chat_id'],
        'text': {'$regex': pattern, '$options': 'i'}
    }).sort("names", 1)

    if not (notes := await notes.to_list(length=300)):
        return await message.reply(strings["notelist_no_notes"].format(chat_title=chat['chat_title']))

    notes_list = []
    for note in notes:
        note_txt = ''
        for note_name in note['names']:
            note_txt += f" <code>#{note_name}</code>"
    notes_list.append(note_txt)

    sec += SList(note_txt)
    doc += sec
    doc += strings['you_can_get_note'].format(note_name='note_name')

    return await message.reply(str(doc))


@register(CommandStart(re.compile('notes')))
@get_strings_dec('notes')
async def private_notes_func(message, strings):
    args = message.get_args().split('_')
    chat_id = args[1]
    keyword = args[2] if args[2] != 'None' else None
    await set_connected_command(message.from_user.id, int(chat_id), ['get', 'notes'])
    chat = (await db.chat_list.find_one({'chat_id': int(chat_id)}))
    msg = await message.answer(strings['privatenotes_notif'].format(chat=chat['chat_title']))
    await get_notes_list(msg, chat, keyword=keyword)
