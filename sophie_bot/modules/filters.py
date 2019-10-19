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

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types.inline_keyboard import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

from sophie_bot import WHITELISTED, decorator, mongodb, redis, dp, bot
from sophie_bot.modules.bans import ban_user, kick_user, mute_user, convert_time, NotEnoughRights
from sophie_bot.modules.connections import connection
from sophie_bot.modules.disable import disablable_dec
from sophie_bot.modules.helper_func.decorators import need_args_dec
from sophie_bot.modules.language import get_string, get_strings_dec, get_strings
from sophie_bot.modules.notes import send_note
from sophie_bot.modules.users import user_admin_dec, user_link, get_chat_admins, user_link_html
from sophie_bot.modules.warns import randomString


# State
class NewFilter(StatesGroup):
    handler = State()
    action = State()
    time = State()
    note_name = State()
    reason = State()
    answer = State()


new_filter_cb = CallbackData('new_filter', 'action')
new_filter_time_cb = CallbackData('select_filter_time', 'time')


@decorator.register()
async def check_message(message):
    chat_id = message.chat.id
    filters = redis.lrange('filters_cache_{}'.format(chat_id), 0, -1)
    if not filters:
        update_handlers_cache(chat_id)
        filters = redis.lrange('filters_cache_{}'.format(chat_id), 0, -1)
    if redis.llen('filters_cache_{}'.format(chat_id)) == 0:
        return
    text = message.text
    if text.split()[0][1:] == 'delfilter':
        return
    for keyword in filters:
        # keyword = keyword.decode("utf-8")
        keyword = re.escape(keyword)
        keyword = keyword.replace(r'\(\+\)', '.*')
        pattern = r"( |^|[^\w])" + keyword + r"( |$|[^\w])"
        if re.search(pattern, text, flags=re.IGNORECASE):
            filter = mongodb.filters_v2.find_one(
                {'chat_id': chat_id, "handler": {'$regex': keyword}})
            if not filter:
                update_handlers_cache(chat_id)
                return
            await do_filter_action(message, filter)


@get_strings_dec("filters")
async def do_filter_action(message, strings, filter):
    chat_id = message.chat.id
    user_id = message.from_user.id
    action = filter['action']
    handler = filter['handler']

    msg_to_answer = message.message_id

    if 'del_msg' in filter and filter['del_msg'] is True or action == 'delmsg':
        # TODO: Check self right to del msg
        await message.delete()
        msg_to_answer = None
    try:
        if action == 'delmsg':
            return
        elif action == 'note':
            await send_note(chat_id, chat_id, msg_to_answer, filter['note_name'], show_none=True)
        elif action == 'answer':
            await bot.send_message(chat_id, filter['answer'], reply_to_message_id=msg_to_answer)
        elif action == 'warn':
            await warn_user_filter(message, filter, user_id, chat_id, msg_to_answer)
        elif action == 'ban':
            ban_time = None
            text = strings['filter_ban_success'].format(
                user=await user_link_html(user_id),
                filter=handler
            )
            if 'time' in filter and filter['time'] is not False:
                ban_time, unit = await convert_time(message, filter['time'])
                text = strings['filter_tban_success'].format(
                    user=await user_link_html(user_id),
                    time=filter['time'][:-1],
                    unit=unit,
                    filter=handler
                )

            if await ban_user(message, user_id, chat_id, ban_time, no_msg=True) is True:
                await bot.send_message(chat_id, text, reply_to_message_id=msg_to_answer)
        elif action == 'mute':
            mute_time = None
            text = strings['filter_mute_success'].format(
                user=await user_link_html(user_id),
                filter=handler
            )
            if 'time' in filter and filter['time'] is not False:
                mute_time, unit = await convert_time(message, filter['time'])
                text = strings['filter_tmute_success'].format(
                    user=await user_link_html(user_id),
                    time=filter['time'][:-1],
                    unit=unit,
                    filter=handler
                )

            if await mute_user(message, user_id, chat_id, mute_time) is True:
                await bot.send_message(chat_id, text, reply_to_message_id=msg_to_answer)
        elif action == 'kick':
            text = strings['filter_kick_success'].format(
                user=await user_link_html(user_id),
                filter=handler
            )
            if await kick_user(message, user_id, chat_id, no_msg=True) is True:
                await bot.send_message(chat_id, text, reply_to_message_id=msg_to_answer)
        else:
            text = "This action isn't supported yet!"
            await bot.send_message(chat_id, text, reply_to_message_id=msg_to_answer)
    except NotEnoughRights:
        text = strings['not_enoff_rights']
        await bot.send_message(chat_id, text, reply_to_message_id=msg_to_answer)


@dp.callback_query_handler(regexp='cancel', state='*')
async def cancel_handler(query, state):
    await state.finish()
    await bot.delete_message(query.message.chat.id, query.message.message_id)


# You can use state '*' if you need to handle all states
@dp.message_handler(commands=['cancel'], state='*')
async def cancel_handle1r(message: types.Message, state: FSMContext):
    # Cancel state and inform user about it
    await state.finish()
    # And remove keyboard (just in case)
    await message.reply('Cancelled.')


@decorator.register(cmds='addfilter', allow_kwargs=True)
@user_admin_dec
@connection(admin=True)
@get_strings_dec("filters")
async def new_filter(message, strings, status, chat_id, chat_title, state=False, **kwargs):
    await state.finish()
    await NewFilter.handler.set()
    await message.reply(strings['write_keyword'])


@dp.message_handler(state=NewFilter.handler)
@dp.callback_query_handler(regexp='add_filter_actions', state='*')
@dp.callback_query_handler(regexp='add_filter_actions_del_msg', state='*')
@get_strings_dec("filters")
@connection(admin=True)
async def add_filter_handler(message, status, chat_id, chat_title, strings, state,
                             del_msg=False, edit=False, **kwargs):
    if 'message' in message:
        query = message
        message = message.message
        edit = message.message_id

    handler = message.text
    real_chat_id = message.chat.id
    async with state.proxy() as data:
        data['chat_id'] = chat_id
        if 'handler' in data:
            handler = data['handler']
        else:
            data['handler'] = handler

        if 'query' in locals() and query.data == 'add_filter_actions_del_msg':
            del_msg = True
            data['del_msg'] = True

    await NewFilter.action.set()
    text = strings['handler_added'].format(handler=handler)
    text += strings['select_action']

    buttons = InlineKeyboardMarkup(row_width=2)

    buttons.add(
        InlineKeyboardButton(
            strings['action_note'],
            callback_data=new_filter_cb.new(action='note')),
        InlineKeyboardButton(
            strings['action_answer'],
            callback_data=new_filter_cb.new(action='answer')),
        InlineKeyboardButton(
            strings['action_delmsg'],
            callback_data=new_filter_cb.new(action='delmsg')),
        InlineKeyboardButton(
            strings['action_warn'],
            callback_data=new_filter_cb.new(action='warn')),
        InlineKeyboardButton(
            strings['action_ban'],
            callback_data=new_filter_cb.new(action='ban')),
        InlineKeyboardButton(
            strings['action_mute'],
            callback_data=new_filter_cb.new(action='mute')),
        InlineKeyboardButton(
            strings['action_kick'],
            callback_data=new_filter_cb.new(action='kick'))
    )

    if del_msg is False:
        buttons.add(
            InlineKeyboardButton(strings['del_origin_off'],
                                 callback_data='add_filter_actions_del_msg')
        )
    else:
        buttons.add(
            InlineKeyboardButton(strings['del_origin_on'],
                                 callback_data='add_filter_actions')
        )

    buttons.add(
        InlineKeyboardButton(strings['exit'], callback_data='cancel')
    )

    if edit is False:
        await message.reply(text, reply_markup=buttons)
    else:
        await bot.edit_message_text(text, real_chat_id, edit, reply_markup=buttons)


@dp.callback_query_handler(new_filter_cb.filter(), state='*')
@get_strings_dec("filters")
async def add_filter_action(query, strings, callback_data, state):
    action = callback_data['action']
    chat_id = query.message.chat.id
    msg_id = query.message.message_id

    async with state.proxy() as data:
        data['action'] = action

    actions_with_timer = ('ban', 'mute')
    actions_with_reason = 'warn'

    if action in actions_with_timer:
        await select_time(state, strings, action, chat_id, msg_id)
    elif action in actions_with_reason:
        await NewFilter.reason.set()
        text = strings['write_reason']
        await bot.edit_message_text(text, chat_id, msg_id)
    elif action == 'note':
        await NewFilter.note_name.set()
        text = strings['write_notename']
        await bot.edit_message_text(text, chat_id, msg_id)
    elif action == 'answer':
        await NewFilter.answer.set()
        text = strings['write_text']
        await bot.edit_message_text(text, chat_id, msg_id)
    else:
        async with state.proxy() as data:
            await filter_added(chat_id, msg_id, data, edit=True)
            await state.finish()


async def select_time(state, strings, action, chat_id, msg_id):
    async with state.proxy() as data:
        data['time_sel_msg'] = msg_id

    await NewFilter.time.set()  # For manual select time

    text = strings['select_time']
    text += strings['select_time_tip']
    text += strings['select_time_btns']
    buttons = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton(
            strings['time_f'], callback_data=new_filter_time_cb.new(time=False)),
        InlineKeyboardButton(
            strings['time_2h'], callback_data=new_filter_time_cb.new(time='2h')),
        InlineKeyboardButton(
            strings['time_5h'], callback_data=new_filter_time_cb.new(time='5h')),
        InlineKeyboardButton(
            strings['time_24h'], callback_data=new_filter_time_cb.new(time='24h')),
        InlineKeyboardButton(
            strings['time_2d'], callback_data=new_filter_time_cb.new(time='2d')),
        InlineKeyboardButton(
            strings['time_1w'], callback_data=new_filter_time_cb.new(time='7d'))
    )

    buttons.add(
        InlineKeyboardButton(strings['back'], callback_data='add_filter_actions')
    )

    buttons.add(
        InlineKeyboardButton(strings['exit'], callback_data='cancel')
    )

    await bot.edit_message_text(text, chat_id, msg_id, reply_markup=buttons)
    return


@dp.callback_query_handler(new_filter_time_cb.filter(), state='*')
async def add_filter_time(query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    time = callback_data['time']
    async with state.proxy() as data:
        data['time'] = time
        await filter_added(query.message.chat.id, query.message.message_id, data, edit=True)
        await state.finish()


@dp.message_handler(state=NewFilter.time)
@get_strings_dec("filters")
async def add_filter_time_manual(message, strings, state, **kwargs):
    text = message.text
    if not any(text.endswith(unit) for unit in ('m', 'h', 'd')):
        text = strings['time_not_valid']
        await bot.send_message(message.chat.id, text, reply_to_message_id=message.message_id)
        await state.finish()
        return
    async with state.proxy() as data:
        data['time'] = text
        await filter_added(message.chat.id, message.message_id, data)
        await state.finish()


@dp.message_handler(state=NewFilter.reason)
async def add_filter_reason(message, state):
    reason = message.text
    async with state.proxy() as data:
        data['reason'] = reason
        await filter_added(message.chat.id, message.message_id, data)
        await state.finish()


@dp.message_handler(state=NewFilter.answer)
async def add_filter_answer(message, state, **args):
    answer = message.text
    async with state.proxy() as data:
        data['answer'] = answer
        await filter_added(message.chat.id, message.message_id, data)
        await state.finish()


@dp.message_handler(state=NewFilter.note_name)
@get_strings_dec("filters")
async def add_filter_note(message, strings, state, **args):
    note_name = message.text.lower()
    async with state.proxy() as data:
        chat_id = data['chat_id']
        if not mongodb.notes.find_one({'chat_id': chat_id, 'name': note_name}):
            await state.finish()
            text = strings['cant_find_note']
            await bot.send_message(message.chat.id, text, reply_to_message_id=message.message_id)
            return
        data['note_name'] = note_name
        await filter_added(message.chat.id, message.message_id, data)
        await state.finish()


async def filter_added(real_chat_id, msg_id, data, edit=False):
    strings = get_strings(real_chat_id, module='filters')
    if await add_new_filter(**data) is True:
        text = strings['filter_added']
    else:
        text = strings['filter_updated']

    chat_title = mongodb.chat_list.find_one({
        'chat_id': int(data['chat_id'])})['chat_title']

    text += strings['new_filter_chat'].format(chat_title=chat_title)
    text += strings['new_filter_handler'].format(handler=data['handler'])
    text += strings['new_filter_action'].format(action=data['action'])
    if 'del_msg' in data and data['del_msg'] is True:
        text += strings['new_filter_also_del_msg']
    if 'time' in data and not data['time'] == 'False':
        text += strings['new_filter_time'].format(time=data['time'])
    if 'note_name' in data:
        text += strings['new_filter_note'].format(note=data['note_name'])
    if 'reason' in data:
        text += strings['new_filter_reason'] + '<code>' + data['reason'] + '</code>'

    if edit is True:
        await bot.edit_message_text(text, real_chat_id, msg_id)
    else:
        await bot.send_message(real_chat_id, text, reply_to_message_id=msg_id)


async def add_new_filter(**data):
    old = mongodb.filters_v2.find_one({'chat_id': data['chat_id'], 'handler': data['handler']})
    if old:
        mongodb.filters_v2.delete_one({'_id': old['_id']})
    check = mongodb.filters_v2.insert_one(data)
    update_handlers_cache(data['chat_id'])
    if hasattr(check, 'upserted_id'):
        return True
    return False


@decorator.register(cmds="filters")
@disablable_dec("filters")
@connection()
@get_strings_dec("filters")
async def list_filters(message, strings, status, chat_id, chat_title):
    filters = mongodb.filters_v2.find({'chat_id': chat_id})
    update_handlers_cache(chat_id)
    if not filters:
        await message.reply(strings["no_filters_in"].format(chat_title))
        return

    text = strings["filters_in"].format(chat_name=chat_title)
    H = 0

    for filter in filters:
        H += 1
        text += f"{H}. {filter['handler']} ({filter['action']})"
        text += "\n"

    await message.reply(text)


@decorator.register(cmds="delfilter")
@need_args_dec()
@user_admin_dec
@need_args_dec()
@connection(admin=True)
@get_strings_dec("filters")
async def del_filter(message, strings, status, chat_id, chat_title):
    handler = message.get_args()
    if handler.isdigit() and 100 > int(handler) > 0:
        filters = mongodb.filters_v2.find({'chat_id': chat_id})
        if filters.count() < int(handler) - 1:
            await message.reply("Bad integer!")
            return
        filter_data = filters[int(handler) - 1]
    else:
        filter_data = mongodb.filters_v2.find_one({'chat_id': chat_id,
                                                   "handler": {'$regex': str(handler)}})
    if not filter_data:
        await message.reply(strings["cant_find_filter"])
        return
    mongodb.filters_v2.delete_one({'_id': filter_data['_id']})
    update_handlers_cache(chat_id)
    text = strings["filter_deleted"]
    text = text.format(filter=filter_data['handler'], chat_name=chat_title)
    await message.reply(text)


def update_handlers_cache(chat_id):
    filters = mongodb.filters_v2.find({'chat_id': chat_id})
    redis.delete('filters_cache_{}'.format(chat_id))
    for filter in filters:
        redis.lpush('filters_cache_{}'.format(chat_id), filter['handler'])


async def warn_user_filter(message, filter, user_id, chat_id, msg_to_answer):
    if user_id in WHITELISTED or user_id in await get_chat_admins(chat_id):
        return

    warn_limit = mongodb.warnlimit.find_one({'chat_id': chat_id})
    db_warns = mongodb.warns.find({
        'user_id': user_id,
        'group_id': chat_id
    })

    #  to avoid adding useless another warn in db
    current_warns = 1

    for _ in db_warns:
        current_warns += 1

    if not warn_limit:
        warn_limit = 3
    else:
        warn_limit = int(warn_limit['num'])

    if current_warns >= warn_limit:
        if await ban_user(message, user_id, chat_id, None) is False:
            print(f'cannot ban user {user_id}')
            return

        await ban_user(message, user_id, chat_id, None, no_msg=False)
        mongodb.warns.delete_many({
            'user_id': user_id,
            'group_id': chat_id
        })

        txt = get_string("filters", "filter_warn_ban", chat_id).format(
            warns=warn_limit,
            user=await user_link(user_id),
            reason=filter['reason']
        )

        await bot.send_message(chat_id, txt, reply_to_message_id=msg_to_answer)
        return
    else:
        rndm = randomString(15)

        mongodb.warns.insert_one({
            'warn_id': rndm,
            'user_id': user_id,
            'group_id': chat_id,
            'reason': filter['reason']
        })

        buttons = InlineKeyboardMarkup().add(InlineKeyboardButton(
            "⚠️ Remove warn", callback_data='remove_warn_{}'.format(rndm)
        ))
        rules = mongodb.rules.find_one({"chat_id": chat_id})

        if rules:
            InlineKeyboardMarkup().add(InlineKeyboardButton(
                "📝 Rules", callback_data='get_note_{}_{}'.format(chat_id, rules['note'])
            ))

        chat_title = mongodb.chat_list.find_one({'chat_id': chat_id})['chat_title']

        txt = get_string("filters", "filter_warn_warned", chat_id).format(
            user=await user_link_html(user_id),
            chat=chat_title,
            handler=filter['handler'],
            current_warns=current_warns,
            max_warns=warn_limit,
            reason=filter['reason']
        )

        await bot.send_message(chat_id, txt, reply_to_message_id=msg_to_answer, reply_markup=buttons)
        return
