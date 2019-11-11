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
    get_parsed_msg,
    get_msg_parse,
    get_reply_msg_btns_text,
    get_msg_file,
    button_parser
)

from sophie_bot.decorator import register
from sophie_bot.services.mongo import db, mongodb
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

    note = {'name': note_name, 'chat_id': chat_id}

    if "reply_to_message" in message:
        # Get parsed reply msg text
        text, note['parse_mode'] = get_parsed_msg(message.reply_to_message)
        # Get parsed origin msg text
        text += ' '
        text += get_parsed_msg(message)[0].partition(
            message.get_command() + ' ' + get_arg(message)
        )[2][1:]
        # Set parse_mode if origin msg override it
        if mode := get_msg_parse(message.text, default_md=False):
            note['parse_mode'] = mode

        # Get message keyboard
        if 'reply_markup' in message.reply_to_message and 'inline_keyboard' in message.reply_to_message.reply_markup:
            text += get_reply_msg_btns_text(message.reply_to_message)

        # Check on attachment
        if msg_file := get_msg_file(message.reply_to_message):
            note['file'] = msg_file
    else:
        text, note['parse_mode'] = get_parsed_msg(message)
        text = text.partition(note_name)[2][1:]

        # Check on attachment
        if msg_file := get_msg_file(message):
            note['file'] = msg_file

    # Notes settings
    if '$PREVIEW' in text:
        note['preview'] = True

    if text.replace(' ', ''):
        note['text'] = text

    if not text and 'file' not in note:
        await message.reply(strings['blank_note'])
        return

    if (await db.notes_v2.replace_one({'name': note_name, 'chat_id': chat_id}, note, upsert=True)).modified_count == 0:
        text = strings['note_saved']
    else:
        text = strings['note_updated']

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

    text, markup = button_parser(chat_id, text)

    if 'parse_mode' in db_item:
        if db_item['parse_mode'] == 'html':
            parse = ParseMode.HTML
        elif db_item['parse_mode'] == 'none':
            parse = None
        elif db_item['parse_mode'] == 'md':
            parse = ParseMode.MARKDOWN
    else:
        parse = ParseMode.MARKDOWN

    print(parse)

    if 'file' in db_item:
        file_id = db_item['file']['id']
        file_type = db_item['file']['type']

        args = (chat_id, file_id)
        kwargs = {'caption': text, 'reply_to_message_id': rpl_id, 'reply_markup': markup}

        if file_type == 'document':
            await bot.send_document(*args, **kwargs)
        elif file_type == 'photo':
            await bot.send_photo(*args, **kwargs)
        elif file_type == 'sticker':
            await bot.send_sticker(*args, **kwargs)
        else:
            with configure_scope() as scope:
                scope.set_extra("db_item", str(db_item))
            raise InvalidFileType
    else:
        try:
            await bot.send_message(
                chat_id,
                text,
                parse_mode=parse,
                disable_web_page_preview=parse,
                reply_to_message_id=rpl_id,
                reply_markup=markup
            )
        except CantParseEntities:
            await bot.send_message(
                chat_id,
                strings['cant_parse_html'],
                reply_to_message_id=rpl_id,
                parse_mode=ParseMode.MARKDOWN
            )
            return


@register(cmds='get')
@need_args_dec()
@chat_connection()
@get_strings_dec('notes')
async def get_note(message, chat, strings):
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

    notes = db.notes_v2.find({'chat_id': chat['chat_id']}).sort("name", 1)
    for note in (check := await notes.to_list(length=300)):
        text += f"- <code>#{note['name']}</code>\n"
    if not check:
        await message.reply(strings["notelist_no_notes"])
        return
    await message.reply(text)
