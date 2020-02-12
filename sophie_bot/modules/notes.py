# Copyright (C) 2019 The Raphielscape Company LLC.
# Copyright (C) 2018 - 2020 MrYacha
#
# This file is part of SophieBot.
#
# SophieBot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.

import difflib
import re
from datetime import datetime

from babel.dates import format_datetime
from pymongo import ReplaceOne

from aiogram.dispatcher.filters.builtin import CommandStart
from aiogram.types.inline_keyboard import InlineKeyboardMarkup, InlineKeyboardButton

from .utils.connections import chat_connection
from .utils.disable import disablable_dec
from .utils.language import get_strings_dec
from .utils.notes import BUTTONS, ALLOWED_COLUMNS, get_parsed_note_list, t_unparse_note_item, send_note
from .utils.message import get_arg, need_args_dec
from .utils.user_details import get_user_link

from sophie_bot import bot
from sophie_bot.decorator import register
from sophie_bot.services.mongo import db
from sophie_bot.services.redis import redis
from sophie_bot.services.telethon import tbot

RESTRICTED_SYMBOLS_IN_NOTENAMES = [':', '**', '__', '`', '#', '"', '[', ']', "'", '$']


@register(cmds='save', user_admin=True)
@need_args_dec()
@chat_connection(admin=True)
@get_strings_dec('notes')
async def save_note(message, chat, strings):
    chat_id = chat['chat_id']
    arg = get_arg(message).lower()
    if arg[0] == '#':
        arg = arg[1:]

    note_names = arg.split('|')

    if any((sym := s) in note_names for s in RESTRICTED_SYMBOLS_IN_NOTENAMES):
        await message.reply(strings['notename_cant_contain'].format(symbol=sym))
        return

    note = await get_parsed_note_list(message)

    note['names'] = note_names
    note['chat_id'] = chat_id

    if 'text' not in note and 'file' not in note:
        await message.reply(strings['blank_note'])
        return

    if old_note := await db.notes_v2.find_one({'chat_id': chat_id, 'names': {'$in': note_names}}):
        text = strings['note_updated']
        note['created_date'] = old_note['created_date']
        note['created_user'] = old_note['created_user']
        note['edited_date'] = datetime.now()
        note['edited_user'] = message.from_user.id
    else:
        text = strings['note_saved']
        note['created_date'] = datetime.now()
        note['created_user'] = message.from_user.id

    await db.notes_v2.replace_one({'_id': old_note['_id']} if old_note else note, note, upsert=True)

    text += strings['you_can_get_note']
    text = text.format(note_name=note_names[0], chat_title=chat['chat_title'])
    if len(note_names) > 1:
        text += strings['note_aliases']
        for notename in note_names:
            text += f' <code>#{notename}</code>'

    await message.reply(text)


@get_strings_dec('notes')
async def get_note(message, strings, note_name=None, db_item=None,
                   chat_id=None, send_id=None, rpl_id=None, noformat=False, event=None):
    if not chat_id:
        chat_id = message.chat.id

    if not send_id:
        send_id = chat_id

    if rpl_id is False:
        rpl_id = None
    elif not rpl_id:
        rpl_id = message.message_id

    if not db_item and not (db_item := await db.notes_v2.find_one({'chat_id': chat_id, 'names': {'$in': [note_name]}})):
        await bot.send_message(
            chat_id,
            strings['no_note'],
            reply_to_message_id=rpl_id
        )
        return

    text, kwargs = await t_unparse_note_item(message, db_item, chat_id, noformat=noformat, event=event)
    kwargs['reply_to'] = rpl_id

    await send_note(send_id, text, **kwargs)


@register(cmds='get')
@disablable_dec('get')
@need_args_dec()
@chat_connection()
@get_strings_dec('notes')
async def get_note_cmd(message, chat, strings):
    note_name = get_arg(message).lower()
    if note_name[0] == '#':
        note_name = note_name[1:]

    if 'reply_to_message' in message:
        rpl_id = message.reply_to_message.message_id
    else:
        rpl_id = message.message_id

    if not (note := await db.notes_v2.find_one({'chat_id': chat['chat_id'], 'names': {'$in': [note_name]}})):
        text = strings['cant_find_note'].format(chat_name=chat['chat_title'])
        all_notes = []
        async for note in db.notes_v2.find({'chat_id': chat['chat_id']}):
            for note_name in note['names']:
                all_notes.append(note_name)
        if len(all_notes) > 0:
            check = difflib.get_close_matches(note_name, all_notes)
            if len(check) > 0:
                text += strings['u_mean'].format(note_name=check[0])
        await message.reply(text)
        return

    arg2 = message.text.split(note_name)[1][1:].lower()
    noformat = True if 'noformat' == arg2 or 'raw' == arg2 else False

    await get_note(message, db_item=note, rpl_id=rpl_id, noformat=noformat)


@register(regexp='^#(\w+)', allow_kwargs=True)
@disablable_dec('get')
@chat_connection()
@get_strings_dec('notes')
async def get_note_hashtag(message, chat, strings, regexp=None, **kwargs):
    note_name = regexp.group(1).lower()
    if not (note := await db.notes_v2.find_one({'chat_id': chat['chat_id'], 'names': {'$in': [note_name]}})):
        return

    if 'reply_to_message' in message:
        rpl_id = message.reply_to_message.message_id
    else:
        rpl_id = message.message_id

    await get_note(message, db_item=note, rpl_id=rpl_id)


@register(cmds=['notes', 'saved'])
@disablable_dec('notes')
@chat_connection()
@get_strings_dec('notes')
async def get_notes_list(message, chat, strings):
    text = strings["notelist_header"].format(chat_name=chat['chat_title'])

    notes = await db.notes_v2.find({'chat_id': chat['chat_id']}).sort("names", 1).to_list(length=300)
    if not notes:
        await message.reply(strings["notelist_no_notes"].format(chat_title=chat['chat_title']))
        return

    # Search
    if len(request := message.get_args()) > 0:
        text += strings['notelist_search'].format(request=request)
        all_notes = notes
        notes = []
        for note in all_notes:
            for note_name in note['names']:
                if re.search(request, note_name):
                    notes.append(note)
        if not len(notes) > 0:
            await message.reply(strings['no_notes_pattern'] % request)
            return

    for note in notes:
        text += '\n-'
        for note_name in note['names']:
            text += f" <code>#{note_name}</code>"
    text += strings['you_can_get_note']
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
    }).sort("names", 1)
    for note in (check := await notes.to_list(length=300)):
        text += '\n-'
        for note_name in note['names']:
            text += f" <code>#{note_name}</code>"
    text += strings['you_get_note']
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

    if not (note := await db.notes_v2.find_one({'chat_id': chat['chat_id'], 'names': {'$in': [note_name]}})):
        text = strings['cant_find_note'].format(chat_name=chat['chat_title'])
        all_notes = []
        async for note in db.notes_v2.find({'chat_id': chat['chat_id']}):
            for note_name in note['names']:
                all_notes.append(note_name)
        if len(all_notes) > 0:
            check = difflib.get_close_matches(note_name, all_notes)
            if len(check) > 0:
                text += strings['u_mean'].format(note_name=check[0])
        await message.reply(text)
        return

    await db.notes_v2.delete_one({'_id': note['_id']})
    await message.reply(strings['note_removed'].format(note_name=note_name, chat_name=chat['chat_title']))


@register(cmds='clearall')
@chat_connection(admin=True)
@get_strings_dec('notes')
async def clear_all_notes(message, chat, strings):
    # Ensure notes count
    if not await db.notes_v2.find_one({'chat_id': chat['chat_id']}):
        await message.reply(strings['notelist_no_notes'].format(chat_title=chat['chat_title']))
        return

    text = strings['clear_all_text'].format(chat_name=chat['chat_title'])
    buttons = InlineKeyboardMarkup()
    buttons.add(InlineKeyboardButton(strings['clearall_btn_yes'], callback_data='clean_all_notes_cb'))
    buttons.add(InlineKeyboardButton(strings['clearall_btn_no'], callback_data='cancel'))
    await message.reply(text, reply_markup=buttons)


@register(regexp='clean_all_notes_cb', f='cb')
@chat_connection(admin=True)
@get_strings_dec('notes')
async def clear_all_notes_cb(event, chat, strings):
    num = (await db.notes_v2.delete_many({'chat_id': chat['chat_id']})).deleted_count

    text = strings['clearall_done'].format(num=num, chat_name=chat['chat_title'])
    await event.message.edit_text(text)


@register(cmds='noteinfo', user_admin=True)
@chat_connection()
@get_strings_dec('notes')
async def note_info(message, chat, strings):
    note_name = get_arg(message).lower()
    if note_name[0] == '#':
        note_name = note_name[1:]

    if not (note := await db.notes_v2.find_one({'chat_id': chat['chat_id'], 'names': {'$in': [note_name]}})):
        text = strings['cant_find_note'].format(chat_name=chat['chat_title'])
        all_notes = []
        async for note in db.notes_v2.find({'chat_id': chat['chat_id']}):
            for note_name in note['names']:
                all_notes.append(note_name)
        if len(all_notes) > 0:
            check = difflib.get_close_matches(note_name, all_notes)
            if len(check) > 0:
                text += strings['u_mean'].format(note_name=check[0])
        await message.reply(text)
        return

    text = strings['note_info_title']

    note_names = ''
    for note_name in note['names']:
        note_names += f" <code>#{note_name}</code>"

    text += strings['note_info_note'] % note_names
    text += strings['note_info_content'] % ('text' if 'file' not in note else note['file']['type'])

    if 'parse_mode' not in note or note['parse_mode'] == 'md':
        parse_mode = 'Markdown'
    elif note['parse_mode'] == 'html':
        parse_mode = 'HTML'
    elif note['parse_mode'] == 'none':
        parse_mode = 'None'
    else:
        raise TypeError()

    text += strings['note_info_parsing'] % parse_mode

    text += strings['note_info_created'].format(
        date=format_datetime(note['created_date'], locale=strings['language_info']['babel']),
        user=await get_user_link(note['created_user'])
    )

    if 'edited_date' in note:
        text += strings['note_info_updated'].format(
            date=format_datetime(note['edited_date'], locale=strings['language_info']['babel']),
            user=await get_user_link(note['edited_user'])
        )

    await message.reply(text)


BUTTONS.update({'note': 'btnnotesm'})


@register(regexp=r'btnnotesm_(\w+)_(.*)', f='cb', allow_kwargs=True)
@get_strings_dec('notes')
async def note_btn(event, strings, regexp=None, **kwargs):
    chat_id = int(regexp.group(2))
    user_id = event.from_user.id
    note_name = regexp.group(1).lower()

    if not (note := await db.notes_v2.find_one({'chat_id': chat_id, 'names': {'$in': [note_name]}})):
        await event.answer(strings['no_note'])
        return

    await event.message.delete()
    await get_note(event.message, db_item=note, chat_id=chat_id, send_id=user_id, rpl_id=None, event=event)


@register(CommandStart(re.compile(r'btnnotesm')), allow_kwargs=True)
@get_strings_dec('notes')
async def note_start(message, strings, regexp=None, **kwargs):
    args = message.get_args().split('_')
    chat_id = int(args[2])
    user_id = message.from_user.id
    note_name = args[1].lower()

    if not (note := await db.notes_v2.find_one({'chat_id': chat_id, 'names': {'$in': [note_name]}})):
        await message.reply(strings['no_note'])
        return

    await get_note(message, db_item=note, chat_id=chat_id, send_id=user_id, rpl_id=None)


@register(cmds='start', only_pm=True)
@get_strings_dec('connections')
async def btn_note_start_state(message, strings):
    key = 'btn_note_start_state:' + str(message.from_user.id)
    if not (cached := redis.hgetall(key)):
        return

    chat_id = int(cached['chat_id'])
    user_id = message.from_user.id
    note_name = cached['notename']

    note = await db.notes_v2.find_one({'chat_id': chat_id, 'names': {'$in': [note_name]}})
    await get_note(message, db_item=note, chat_id=chat_id, send_id=user_id, rpl_id=None)

    redis.delete(key)


async def __stats__():
    text = "* <code>{}</code> total notes\n".format(
        await db.notes_v2.count_documents({})
    )
    return text


async def __export__(chat_id):
    data = []
    notes = await db.notes_v2.find({'chat_id': chat_id}).sort("names", 1).to_list(length=300)
    for note in notes:
        del note['_id']
        del note['chat_id']
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
    new = []
    for note in data:

        # File ver 1 to 2
        if 'name' in note:
            note['names'] = [note['name']]
            del note['name']

        for item in [i for i in note if i not in ALLOWED_COLUMNS_NOTES]:
            del note[item]

        note['chat_id'] = chat_id
        new.append(ReplaceOne({'chat_id': note['chat_id'], 'names': {'$in': [note['names'][0]]}}, note, upsert=True))

    await db.notes_v2.bulk_write(new)
