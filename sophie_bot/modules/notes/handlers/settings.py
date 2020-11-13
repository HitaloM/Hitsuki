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

from sophie_bot.decorator import register
from sophie_bot.services.mongo import db
from ...utils.connections import chat_connection
from ...utils.language import get_strings_dec
from ...utils.message import get_arg


@register(cmds=['privatenotes', 'pmnotes'], is_admin=True)
@chat_connection(admin=True)
@get_strings_dec('notes')
async def private_notes_cmd(message, chat, strings):
    chat_id = chat['chat_id']
    chat_name = chat['chat_title']
    text = str

    try:
        (text := ''.join(message.text.split()[1]).lower())
    except IndexError:
        pass

    enabling = ['true', 'enable', 'on']
    disabling = ['false', 'disable', 'off']
    if database := await db.privatenotes.find_one({'chat_id': chat_id}):
        if text in enabling:
            await message.reply(strings['already_enabled'] % chat_name)
            return
    if text in enabling:
        await db.privatenotes.insert_one({'chat_id': chat_id})
        await message.reply(strings['enabled_successfully'] % chat_name)
    elif text in disabling:
        if not database:
            await message.reply(strings['not_enabled'])
            return
        await db.privatenotes.delete_one({'_id': database['_id']})
        await message.reply(strings['disabled_successfully'] % chat_name)
    else:
        # Assume admin asked for current state
        if database:
            state = strings['enabled']
        else:
            state = strings['disabled']
        await message.reply(strings['current_state_info'].format(state=state, chat=chat_name))


@register(cmds='cleannotes', is_admin=True)
@chat_connection(admin=True)
@get_strings_dec('notes')
async def clean_notes(message, chat, strings):
    disable = ['no', 'off', '0', 'false', 'disable']
    enable = ['yes', 'on', '1', 'true', 'enable']

    chat_id = chat['chat_id']

    arg = get_arg(message)
    if arg and arg.lower() in enable:
        await db.clean_notes.update_one({'chat_id': chat_id}, {'$set': {'enabled': True}}, upsert=True)
        text = strings['clean_notes_enable'].format(chat_name=chat['chat_title'])
    elif arg and arg.lower() in disable:
        await db.clean_notes.update_one({'chat_id': chat_id}, {'$set': {'enabled': False}}, upsert=True)
        text = strings['clean_notes_disable'].format(chat_name=chat['chat_title'])
    else:
        data = await db.clean_notes.find_one({'chat_id': chat_id})
        if data and data['enabled'] is True:
            text = strings['clean_notes_enabled'].format(chat_name=chat['chat_title'])
        else:
            text = strings['clean_notes_disabled'].format(chat_name=chat['chat_title'])

    await message.reply(text)
