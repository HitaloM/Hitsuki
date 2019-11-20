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

import asyncio
import ujson
import io

from datetime import datetime, timedelta
from babel.dates import format_timedelta

from aiogram.types.input_file import InputFile

from .utils.connections import chat_connection
from .utils.language import get_strings_dec

from . import LOADED_MODULES

from sophie_bot import OPERATORS
from sophie_bot.decorator import register
from sophie_bot.services.redis import redis


@register(cmds='export', is_admin=True)
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
            'version': 1
        }
    }

    for module in [m for m in LOADED_MODULES if hasattr(m, '__export__')]:
        await asyncio.sleep(0.2)
        data.update(await module.__export__(chat_id))

    jfile = InputFile(io.StringIO(ujson.dumps(data, indent=2)), filename=f'{chat_id}_export.json')
    text = strings['export_done'] % chat['chat_title']
    await message.answer_document(jfile, text, reply=message.message_id)
    await msg.delete()
