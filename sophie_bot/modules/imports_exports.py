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

import asyncio
import io
from datetime import datetime, timedelta

import ujson
from aiogram import types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types.input_file import InputFile
from babel.dates import format_timedelta

from sophie_bot import OPERATORS, bot
from sophie_bot.decorator import register
from sophie_bot.services.redis import redis
from . import LOADED_MODULES
from .utils.connections import chat_connection
from .utils.language import get_strings_dec


# Waiting for import file state
class ImportFileWait(StatesGroup):
    waiting = State()


@register(cmds='export', user_admin=True)
@chat_connection(admin=True, only_groups=True)
@get_strings_dec('imports_exports')
async def export_chat_data(message, chat, strings):
    chat_id = chat['chat_id']
    key = 'export_lock:' + str(chat_id)
    if redis.get(key) and message.from_user.id not in OPERATORS:
        ttl = format_timedelta(timedelta(seconds=redis.ttl(key)), strings['language_info']['babel'])
        await message.reply(strings['exports_locked'] % ttl)
        return

    redis.set(key, 1)
    redis.expire(key, 7200)

    msg = await message.reply(strings['started_exporting'])
    data = {
        'general': {
            'chat_name': chat['chat_title'],
            'chat_id': chat_id,
            'timestamp': datetime.now(),
            'version': 2
        }
    }

    for module in [m for m in LOADED_MODULES if hasattr(m, '__export__')]:
        await asyncio.sleep(0.2)
        if k := await module.__export__(chat_id):
            data.update(k)

    jfile = InputFile(io.StringIO(ujson.dumps(data, indent=2)), filename=f'{chat_id}_export.json')
    text = strings['export_done'] % chat['chat_title']
    await message.answer_document(jfile, text, reply=message.message_id)
    await msg.delete()


@register(cmds='import', user_admin=True)
@get_strings_dec('imports_exports')
async def import_reply(message, strings):
    if 'document' in message:
        document = message.document
    else:
        if 'reply_to_message' not in message:
            await ImportFileWait.waiting.set()
            await message.reply(strings['send_import_file'])
            return

        elif 'document' not in message.reply_to_message:
            await message.reply(strings['rpl_to_file'])
            return
        document = message.reply_to_message.document

    await import_fun(message, document)


@register(state=ImportFileWait.waiting, content_types=types.ContentTypes.DOCUMENT, allow_kwargs=True)
async def import_state(message, state=None, **kwargs):
    await import_fun(message, message.document)
    await state.finish()


@chat_connection(admin=True, only_groups=True)
@get_strings_dec('imports_exports')
async def import_fun(message, document, chat, strings):
    chat_id = chat['chat_id']
    key = 'import_lock:' + str(chat_id)
    if redis.get(key) and message.from_user.id not in OPERATORS:
        ttl = format_timedelta(timedelta(seconds=redis.ttl(key)), strings['language_info']['babel'])
        await message.reply(strings['imports_locked'] % ttl)
        return

    redis.set(key, 1)
    redis.expire(key, 7200)

    msg = await message.reply(strings['started_importing'])
    if document['file_size'] > 52428800:
        await message.reply(strings['big_file'])
        return
    data = await bot.download_file_by_id(document.file_id, io.BytesIO())
    data = ujson.load(data)

    if 'general' not in data:
        await message.reply(strings['bad_file'])
        return

    imported = []
    for module in [m for m in LOADED_MODULES if hasattr(m, '__import__')]:
        module_name = module.__name__.replace('sophie_bot.modules.', '')
        print(module_name)
        if module_name in data:
            imported.append(module_name)
            await asyncio.sleep(0.2)
            await module.__import__(chat_id, data[module_name])

    await msg.delete()
    await message.answer(strings['import_done'], reply=message.message_id)
