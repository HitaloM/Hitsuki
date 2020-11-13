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
from contextlib import suppress

from aiogram.dispatcher.filters.builtin import CommandStart
from aiogram.utils.exceptions import MessageCantBeDeleted

from sophie_bot.decorator import register
from sophie_bot.services.mongo import db
from sophie_bot.services.redis import redis
from ..utils.get import get_note
from ...utils.language import get_strings_dec
from ...utils.notes import BUTTONS

BUTTONS.update({'note': 'btnnotesm', '#': 'btnnotesm'})


@register(regexp=r'btnnotesm_(\w+)_(.*)', f='cb', allow_kwargs=True)
@get_strings_dec('notes')
async def note_btn(event, strings, regexp=None, **kwargs):
    chat_id = int(regexp.group(2))
    user_id = event.from_user.id
    note_name = regexp.group(1).lower()

    if not (note := await db.notes.find_one({'chat_id': chat_id, 'names': {'$in': [note_name]}})):
        await event.answer(strings['no_note'])
        return

    with suppress(MessageCantBeDeleted):
        await event.message.delete()
    await get_note(event.message, db_item=note, chat_id=chat_id, send_id=user_id, rpl_id=None, event=event)


@register(CommandStart(re.compile(r'btnnotesm')), allow_kwargs=True)
@get_strings_dec('notes')
async def note_start(message, strings, regexp=None, **kwargs):
    # Don't even ask what it means, mostly it workaround to support note names with _
    args = re.search(r'^([a-zA-Z0-9]+)_(.*?)(-\d+)$', message.get_args())
    chat_id = int(args.group(3))
    user_id = message.from_user.id
    note_name = args.group(2).strip("_")

    if not (note := await db.notes.find_one({'chat_id': chat_id, 'names': {'$in': [note_name]}})):
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

    note = await db.notes.find_one({'chat_id': chat_id, 'names': {'$in': [note_name]}})
    await get_note(message, db_item=note, chat_id=chat_id, send_id=user_id, rpl_id=None)

    redis.delete(key)
