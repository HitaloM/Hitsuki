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

from aiogram.types.inline_keyboard import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
from aiogram.utils.exceptions import BotBlocked
from aiogram.dispatcher.filters.builtin import CommandStart

from sophie_bot import bot
from sophie_bot.decorator import register
from sophie_bot.services.mongo import db
from sophie_bot.services.redis import redis

from .utils.connections import chat_connection, set_connected_chat
from .utils.language import get_strings_dec
from .utils.message import get_arg
from .utils.notes import BUTTONS
from .utils.user_details import get_chat_dec

connect_to_chat_cb = CallbackData('connect_to_chat_cb', 'chat_id')


@get_strings_dec('connections')
async def def_connect_chat(message, user_id, chat_id, chat_title, strings, edit=False):
    await set_connected_chat(user_id, chat_id)

    text = strings['pm_connected'].format(chat_name=chat_title)
    if edit:
        await message.edit_text(text)
    else:
        await message.reply(text)


# In chat - connect directly to chat
@register(cmds='connect', only_groups=True)
@get_strings_dec('connections')
async def connect_to_chat_direct(message, strings):
    user_id = message.from_user.id
    chat_id = message.chat.id

    chat_title = (await db.chat_list.find_one({'chat_id': chat_id}))['chat_title']
    text = strings['pm_connected'].format(chat_name=chat_title)

    try:
        await bot.send_message(user_id, text)
        await def_connect_chat(message, user_id, chat_id, chat_title)
    except BotBlocked:
        await message.reply(strings['connected_pm_to_me'].format(chat_name=chat_title))
        redis.set('sophie_connected_start_state:' + str(user_id), 1)


# In pm without args - show last connected chats
@register(cmds='connect', no_args=True, only_pm=True)
@get_strings_dec('connections')
@chat_connection()
async def connect_chat_keyboard(message, strings, chat):
    if chat['status'] != 'private':
        text = strings['connected_chat'].format(chat_name=chat['chat_title'])
    else:
        text = ''

    text += strings['select_chat_to_connect']
    markup = InlineKeyboardMarkup(row_width=1)

    if 'history' in (connected := await db.connections_v2.find_one({'user_id': message.from_user.id}, {'history': {'$slice': -3}})):
        for chat_id in reversed(connected['history']):
            chat = await db.chat_list.find_one({'chat_id': chat_id})
            markup.insert(InlineKeyboardButton(
                chat['chat_title'],
                callback_data=connect_to_chat_cb.new(chat_id=chat_id))
            )
    else:
        return await message.reply(strings['u_wasnt_connected'])

    await message.reply(text, reply_markup=markup)


# Callback for prev. function
@register(connect_to_chat_cb.filter(), f='cb', allow_kwargs=True)
async def connect_chat_keyboard_cb(message, callback_data=False, **kwargs):
    chat_id = int(callback_data['chat_id'])
    chat = await db.chat_list.find_one({'chat_id': chat_id})
    await def_connect_chat(message.message, message.from_user.id, chat_id, chat['chat_title'], edit=True)


# In pm with args - connect to chat by arg
@register(cmds='connect', has_args=True, only_pm=True)
@get_chat_dec
@get_strings_dec('connections')
async def connect_to_chat_from_arg(message, chat, strings):
    user_id = message.from_user.id
    chat_id = message.chat.id

    await def_connect_chat(message, user_id, chat_id, chat['chat_title'])


@register(cmds='disconnect', only_pm=True)
@get_strings_dec('connections')
@chat_connection()
async def disconnect_from_chat_direct(message, strings, chat):
    if chat['status'] == 'private':
        await message.reply(strings['u_wasnt_connected'])
        return

    user_id = message.from_user.id
    await set_connected_chat(user_id, None)
    await message.reply(strings['disconnected'].format(chat_name=chat['chat_title']))


@register(cmds='allowusersconnect')
@get_strings_dec('connections')
@chat_connection(admin=True, only_groups=True)
async def allow_users_to_connect(message, strings, chat):
    chat_id = chat['chat_id']
    arg = get_arg(message).lower()
    if not arg:
        status = strings['enabled']
        data = await db.chat_connection_settings.find_one({'chat_id': chat_id})
        if data and 'allow_users_connect' in data and data['allow_users_connect'] is False:
            status = strings['disabled']
        await message.reply(strings['chat_users_connections_info'].format(
            status=status,
            chat_name=chat['chat_title']
        ))
        return
    enable = ('enable', 'on', 'ok', 'yes')
    disable = ('disable', 'off', 'no')
    if arg in enable:
        r_bool = True
        status = strings['enabled']
    elif arg in disable:
        r_bool = False
        status = strings['disabled']
    else:
        await message.reply(strings['bad_arg_bool'])
        return

    await db.chat_connection_settings.update_one(
        {'chat_id': chat_id},
        {"$set": {'allow_users_connect': r_bool}},
        upsert=True
    )
    await message.reply(strings['chat_users_connections_cng'].format(
        status=status,
        chat_name=chat['chat_title']
    ))


@register(cmds='start', only_pm=True)
@get_strings_dec('connections')
@chat_connection()
async def connected_start_state(message, strings, chat):
    key = 'sophie_connected_start_state:' + str(message.from_user.id)
    if redis.get(key):
        await message.reply(strings['pm_connected'].format(chat_name=chat['chat_title']))
        redis.delete(key)


BUTTONS.update({'connect': 'btn_connect_start'})


@register(CommandStart(re.compile(r'btn_connect_start')), allow_kwargs=True)
@get_strings_dec('connections')
async def connect_start(message, strings, regexp=None, **kwargs):
    args = message.get_args().split('_')

    # In case if button have arg it will be used. # TODO: Check chat_id, parse chat nickname.
    arg = args[3]

    if arg.startswith('-') or arg.isdigit():
        chat = await db.chat_list.find_one({'chat_id': int(arg)})
    elif arg.startswith('@'):
        chat = await db.chat_list.find_one({'chat_nick': arg.lower()})
    else:
        await message.reply(strings['cant_find_chat_use_id'])
        return

    await def_connect_chat(message, message.from_user.id, chat['chat_id'], chat['chat_title'])
