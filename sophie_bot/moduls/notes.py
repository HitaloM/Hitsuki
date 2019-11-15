# Copyright (C) 2019 The Raphielscape Company LLC.
# Copyright (C) 2018 - 2019 MrYacha
#
# This file is part of SophieBot.
#
# SophieBot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.

import re
import difflib

from sentry_sdk import configure_scope

from aiogram.types import ParseMode
from aiogram.utils.exceptions import CantParseEntities

from .utils.language import get_strings_dec
from .utils.connections import chat_connection
from .utils.disable import disablable_dec
from .utils.message import (
    need_args_dec,
    get_arg,
    get_args,
    get_parsed_msg,
    get_msg_parse,
    get_reply_msg_btns_text,
    get_msg_file,
    tbutton_parser,
    get_parsed_note_list
)

from sophie_bot.decorator import register
from sophie_bot.services.mongo import db, mongodb
from sophie_bot.services.telethon import tbot
from sophie_bot import bot


class InvalidFileType(Exception):
    pass


@register(cmds='owo', is_owner=True)
async def test_cmds(message):
    print(message)
    print(get_msg_file(message.reply_to_message))


@register(cmds='save', is_admin=True)
@need_args_dec()
@chat_connection(admin=True)
@get_strings_dec('notes')
async def save_note(message, chat, strings):
    chat_id = chat['chat_id']
    note_name = get_arg(message).lower()
    if note_name[0] == '#':
        note_name = note_name[1:]

    note = get_parsed_note_list(message)

    note['name'] = note_name
    note['chat_id'] = chat_id

    if 'text' not in note and 'file' not in note:
        await message.reply(strings['blank_note'])
        return

    # Notes settings
    if 'text' in note and '$PREVIEW' in note['text']:
        note['preview'] = True

    if (await db.notes_v2.replace_one({'name': note_name, 'chat_id': chat_id}, note, upsert=True)).modified_count == 0:
        text = strings['note_saved']
    else:
        text = strings['note_updated']

    # await db.notes_v2.create_index({'name': note_name, 'text': note['name'] or None})

    text += strings['you_can_get_note']
    text = text.format(note_name=note_name, chat_title=chat['chat_title'])

    await message.reply(text)


@get_strings_dec('notes')
async def get_note(message, strings, note_name=None, db_item=None, chat_id=None, rpl_id=None):
    if not chat_id:
        chat_id = message.chat.id

    if rpl_id is False:
        rpl_id = None
    elif not rpl_id:
        rpl_id = message.message_id

    if not db_item and not (db_item := await db.notes_v2.find_one({'name': note_name})):
        await bot.send_message(
            chat_id,
            strings['no_note'],
            reply_to_message_id=rpl_id
        )
        return

    text = db_item['text'] if 'text' in db_item else ""

    text, markup = tbutton_parser(chat_id, text)

    file_id = None
    if 'file' in db_item:
        file_id = db_item['file']['id']

    if 'parse_mode' not in db_item or db_item['parse_mode'] == 'none':
        db_item['parse_mode'] = None

    if 'preview' in db_item and db_item['preview']:
        preview = True
    else:
        preview = False

    await tbot.send_message(
        chat_id,
        text,
        buttons=markup,
        parse_mode=db_item['parse_mode'],
        reply_to=rpl_id,
        file=file_id,
        link_preview=preview
    )


@register(cmds='get')
@need_args_dec()
@chat_connection()
@get_strings_dec('notes')
async def get_note_cmd(message, chat, strings):
    note_name = get_arg(message).lower()
    if note_name[0] == '#':
        note_name = note_name[1:]

    if not (note := await db.notes_v2.find_one({'name': note_name})):
        text = strings['cant_find_note'].format(chat_name=chat['chat_title'])
        all_notes = mongodb.notes_v2.find({'chat_id': chat['chat_id']})
        if all_notes.count() > 0:
            check = difflib.get_close_matches(note_name, [d['name'] for d in all_notes])
            if len(check) > 0:
                text += strings['u_mean'].format(note_name=check[0])
        await message.reply(text)
        return

    await get_note(message, db_item=note)


@register(regexp='^#(\w+)', allow_kwargs=True)
@chat_connection()
@get_strings_dec('notes')
async def get_note_hashtag(message, chat, strings, regexp=None, **kwargs):
    note_name = regexp.group(1).lower()
    if not (note := await db.notes_v2.find_one({'name': note_name})):
        return
    await get_note(message, db_item=note)


@register(cmds=['notes', 'saved'])
@chat_connection()
@get_strings_dec('notes')
async def get_notes_list(message, chat, strings):
    text = strings["notelist_header"].format(chat_name=chat['chat_title'])

    notes = await db.notes_v2.find({'chat_id': chat['chat_id']}).sort("name", 1).to_list(length=300)
    if not notes:
        await message.reply(strings["notelist_no_notes"].format(chat_title=chat['chat_title']))
        return

    # Search
    if len(request := message.get_args()) > 0:
        text += strings['notelist_search'].format(request=request)
        notes = difflib.get_close_matches(request, [d['name'] for d in notes], n=100)
        if not len(notes) > 0:
            await message.reply(strings['no_note'])  # TODO

    for note in notes:
        note_name = note['name'] if type(note) == dict else note
        text += f"- <code>#{note_name}</code>\n"
    text += strings['u_can_get_note']
    await message.reply(text)


@register(cmds='search')
@chat_connection()
@get_strings_dec('notes')
async def search_in_note(message, chat, strings):
    request = message.get_args()
    text = strings["search_header"].format(chat_name=chat['chat_title'], request=request)

    notes = db.notes_v2.find({
        'chat_id': chat['chat_id'],
        'text': {'$regex': request, '$options': 'i'}
    }).sort("name", 1)
    for note in (check := await notes.to_list(length=300)):
        text += f"- <code>#{note['name']}</code>\n"
    text += strings['u_can_get_note']
    if not check:
        await message.reply(strings["notelist_no_notes"].format(chat_title=chat['chat_title']))
        return
    await message.reply(text)


@register(cmds=['clear', 'delnote'])
@chat_connection(admin=True)
@get_strings_dec('notes')
async def clear_note(message, chat, strings):
    note_name = get_arg(message).lower()
    if note_name[0] == '#':
        note_name = note_name[1:]

    if not (note := await db.notes_v2.find_one({'name': note_name})):
        text = strings['cant_find_note'].format(chat_name=chat['chat_title'])
        all_notes = mongodb.notes_v2.find({'chat_id': chat['chat_id']})
        if all_notes.count() > 0:
            check = difflib.get_close_matches(note_name, [d['name'] for d in all_notes])
            if len(check) > 0:
                text += strings['u_mean'].format(note_name=check[0])
        await message.reply(text)
        return

    await db.notes_v2.delete_one({'_id': note['_id']})
    await message.reply(strings['note_removed'].format(note_name=note_name, chat_name=chat['chat_title']))


async def __stats__():
    text = "* <code>{}</code> total notes\n".format(
        await db.notes_v2.count_documents({})
    )
    return text
