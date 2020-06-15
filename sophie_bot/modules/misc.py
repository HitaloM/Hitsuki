# Copyright (C) 2018 - 2020 MrYacha. All rights reserved. Source code available under the AGPL.
# Copyright (C) 2019 Aiogram

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
import html
import random

from aiogram.utils.exceptions import BadRequest, CantParseEntities
from aiogram.utils.exceptions import MessageNotModified, MessageToDeleteNotFound
from contextlib import suppress

from sophie_bot.decorator import register
from .utils.notes import get_parsed_note_list, send_note, t_unparse_note_item
from .utils.user_details import is_user_admin
from .utils.disable import disableable_dec
from .utils.language import get_strings_dec


@register(cmds="runs")
@get_strings_dec("RUNS", mas_name="RANDOM_STRINGS")
@disableable_dec('runs')
async def runs(message, strings):
    text = random.choice(list(strings))
    try:
        await message.reply(text)
    except CantParseEntities:
        await message.reply(html.escape(text))


@register(cmds='cancel', state='*', allow_kwargs=True)
async def cancel_handle(message, state, **kwargs):
    await state.finish()
    await message.reply('Cancelled.')


async def delmsg_filter_handle(message, chat, data):
    if await is_user_admin(data['chat_id'], message.from_user.id):
        return
    with suppress(MessageToDeleteNotFound):
        await message.delete()


async def replymsg_filter_handler(message, chat, data):
    text, kwargs = await t_unparse_note_item(message, data['reply_text'], chat['chat_id'])
    kwargs['reply_to'] = message.message_id
    with suppress(BadRequest):
        await send_note(chat['chat_id'], text, **kwargs)


@get_strings_dec('misc')
async def replymsg_setup_start(message, strings):
    with suppress(MessageNotModified):
        await message.edit_text(strings['send_text'])


async def replymsg_setup_finish(message, data):
    reply_text = await get_parsed_note_list(message, allow_reply_message=False, split_args=-1)
    return {'reply_text': reply_text}


__filters__ = {
    'delete_message': {
        'title': {'module': 'misc', 'string': 'delmsg_filter_title'},
        'handle': delmsg_filter_handle,
        'del_btn_name': lambda msg, data: f"Del message: {data['handler']}"
    },
    'reply_message': {
        'title': {'module': 'misc', 'string': 'replymsg_filter_title'},
        'handle': replymsg_filter_handler,
        'setup': {
            'start': replymsg_setup_start,
            'finish': replymsg_setup_finish
        },
        'del_btn_name': lambda msg, data: f"Reply to {data['handler']}: {data['reply_text']}"
    }
}
