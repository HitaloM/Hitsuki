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

import re

from aiogram.types.inline_keyboard import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.callback_data import CallbackData
from aiogram.dispatcher.filters.state import State, StatesGroup
from bson.objectid import ObjectId

from .utils.message import need_args_dec, get_arg
from .utils.user_details import is_user_admin
from .utils.language import get_strings_dec, get_string
from .utils.connections import chat_connection, get_connected_chat

from sophie_bot.decorator import register
from sophie_bot.modules import LOADED_MODULES
from sophie_bot.utils.logger import log
from sophie_bot.services.mongo import db
from sophie_bot.services.redis import redis
from sophie_bot.utils.logger import log


filter_action_cp = CallbackData('filter_action_cp', 'filter_id')
filter_remove_cp = CallbackData('filter_remove_cp', 'id')

FILTERS_ACTIONS = {}


class NewFilter(StatesGroup):
    handler = State()
    setup = State()


async def update_handlers_cache(chat_id):
    redis.delete(f'filters_cache_{chat_id}')
    filters = db.filters.find({'chat_id': chat_id})
    handlers = []
    async for filter in filters:
        handler = filter['handler']
        if filter in handlers:
            continue

        handlers.append(handler)
        redis.lpush(f'filters_cache_{chat_id}', handler)

    return handlers


@register()
async def check_msg(message):
    log.debug("Running check msg for filters function.")
    chat = await get_connected_chat(message)
    chat_id = chat['chat_id']
    if not (filters := redis.lrange(f'filters_cache_{chat_id}', 0, -1)):
        filters = await update_handlers_cache(chat_id)

    if len(filters) == 0:
        return

    text = message.text

    # Workaround to disable all filters if admin want to remove filter
    if await is_user_admin(chat_id, message.from_user.id) and (text[1:].startswith('addfilter') or
                                                               text[1:].startswith('delfilter')):
        return

    for handler in filters:
        pattern = handler
        if re.search(pattern, text, flags=re.IGNORECASE):

            # We can have few filters with same handler, that's why we create a new loop.
            filters = db.filters.find({'chat_id': chat_id, 'handler': handler})
            async for filter in filters:
                action = filter['action']
                await FILTERS_ACTIONS[action]['handle'](message, chat, filter)


@register(cmds=['addfilter', 'newfilter'], is_admin=True)
@need_args_dec()
@chat_connection(only_groups=True, admin=True)
@get_strings_dec('filters')
async def add_handler(message, chat, strings):
    handler = get_arg(message).lower()
    text = strings['adding_filter'].format(handler=handler, chat_name=chat['chat_title'])

    buttons = InlineKeyboardMarkup(row_width=2)
    for action in FILTERS_ACTIONS.items():
        filter_id = action[0]
        data = action[1]

        buttons.add(InlineKeyboardButton(
            await get_string(chat['chat_id'], data['title']['module'], data['title']['string']),
            callback_data=filter_action_cp.new(filter_id=filter_id)
        ))
    user_id = message.from_user.id
    chat_id = chat['chat_id']
    redis.set(f'add_filter:{user_id}:{chat_id}', handler)
    await message.reply(text, reply_markup=buttons)


async def save_filter(message, data):
    await db.filters.insert_one(data)
    await message.reply('Saved!')


@register(filter_action_cp.filter(), f='cb', is_admin=True, allow_kwargs=True)
@chat_connection(only_groups=True, admin=True)
async def register_action(event, chat, callback_data=None, state=None, **kwargs):
    filter_id = callback_data['filter_id']
    action = FILTERS_ACTIONS[filter_id]

    user_id = event.from_user.id
    chat_id = chat['chat_id']

    handler = redis.get(f'add_filter:{user_id}:{chat_id}')

    data = {
        'chat_id': chat_id,
        'handler': handler,
        'action': filter_id
    }

    if 'setup' in action:
        await NewFilter.setup.set()
        async with state.proxy() as proxy:
            proxy['data'] = data
            proxy['filter_id'] = filter_id

        await action['setup']['start'](event.message)
        return

    await save_filter(event.message, data)


@register(state=NewFilter.setup, is_admin=True, allow_kwargs=True)
@chat_connection(only_groups=True, admin=True)
async def setup_end(message, chat, state=None, **kwargs):
    async with state.proxy() as proxy:
        data = proxy['data']
        filter_id = proxy['filter_id']

    action = FILTERS_ACTIONS[filter_id]

    if not (a := await action['setup']['finish'](message, data)):
        await state.finish()
        return

    data.update(a)

    await state.finish()
    await save_filter(message, data)


@register(cmds=['filters', 'listfilters'])
@chat_connection(only_groups=True)
@get_strings_dec('filters')
async def list_filters(message, chat, strings):
    text = strings['list_filters'].format(chat_name=chat['chat_title'])

    filters = db.filters.find({'chat_id': chat['chat_id']})
    filters_text = ''
    async for filter in filters:
        filters_text += f"- {filter['handler']}: {filter['action']}\n"

    if not filters_text:
        await message.reply(strings['no_filters_found'].format(chat_name=chat['chat_title']))
        return

    await message.reply(text + filters_text)


@register(cmds='delfilter', is_admin=True)
@need_args_dec()
@chat_connection(only_groups=True, admin=True)
@get_strings_dec('filters')
async def del_filter(message, chat, strings):
    handler = get_arg(message).lower()
    chat_id = chat['chat_id']
    filters = await db.filters.find({'chat_id': chat_id, 'handler': handler}).to_list(9999)
    if not filters:
        await message.reply(strings['no_such_filter'].format(chat_name=chat['chat_title']))
        return

    # Remove filter in case if we found only 1 filter with same header
    filter = filters[0]
    if len(filters) == 1:
        await db.filters.delete_one({'id': filter['_id']})
        await update_handlers_cache(chat_id)
        await message.reply(strings['del_filter'].format(handler=filter['handler']))
        return

    # Build keyboard row for select which exactly filter user want to remove
    buttons = InlineKeyboardMarkup(row_width=1)
    text = strings['select_filter_to_remove'].format(handler=handler)
    for filter in filters:
        action = FILTERS_ACTIONS[filter['action']]
        buttons.add(InlineKeyboardButton(
            # If module's filter support custom del btn names else just show action name
            '' + action['del_btn_name'](message, filter) if 'del_btn_name' in action else filter['action'],
            callback_data=filter_remove_cp.new(id=str(filter['_id']))
        ))

    await message.reply(text, reply_markup=buttons)


@register(filter_remove_cp.filter(), f='cb', is_admin=True, allow_kwargs=True)
@chat_connection(only_groups=True, admin=True)
@get_strings_dec('filters')
async def del_filter_cb(event, chat, strings, callback_data=None, **kwargs):
    filter_id = ObjectId(callback_data['id'])
    filter = await db.filters.find_one({'_id': filter_id})
    await db.filters.delete_one({'_id': filter_id})
    await update_handlers_cache(chat['chat_id'])
    await event.message.edit_text(strings['del_filter'].format(handler=filter['handler']))
    return


async def __before_serving__(loop):
    log.debug('Adding filters actions')
    for module in LOADED_MODULES:
        if not getattr(module, '__filters__', None):
            continue

        module_name = module.__name__.split('.')[-1]
        log.debug(f'Adding filter action from {module_name} module')
        for data in module.__filters__.items():
            FILTERS_ACTIONS[data[0]] = data[1]
