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

from babel.dates import format_datetime

from sophie_bot import BOT_ID
from sophie_bot.decorator import register
from sophie_bot.services.telethon import tbot
from sophie_bot.services.redis import redis
from .utils.connections import chat_connection
from .utils.language import get_strings_dec
from .utils.message import InvalidTimeUnit, get_cmd, convert_time
from .utils.restrictions import kick_user, mute_user
from .utils.user_details import get_user_dec, get_user_link, is_user_admin


@register(cmds=['kick', 'skick'], bot_can_restrict_members=True, user_can_restrict_members=True)
@chat_connection(admin=True, only_groups=True)
@get_user_dec()
@get_strings_dec('restrictions')
async def kick_user_cmd(message, chat, user, strings):
    chat_id = chat['chat_id']
    user_id = user['user_id']

    if user_id == BOT_ID:
        await message.reply(strings['kick_sophie'])
        return

    elif user_id == message.from_user.id:
        await message.reply(strings['kick_self'])
        return

    elif await is_user_admin(chat_id, user_id):
        await message.reply(strings['kick_admin'])
        return

    text = strings['user_kicked'].format(
        user=await get_user_link(user_id),
        admin=await get_user_link(message.from_user.id),
        chat_name=chat['chat_title']
    )

    # Add reason
    if len(args := message.get_args().split(' ', 1)) > 1:
        text += strings['reason'] % args[1]

    # Check if silent
    silent = False
    if get_cmd(message) == 'skick':
        silent = True
        key = 'leave_silent:' + str(chat_id)
        redis.set(key, user_id)
        redis.expire(key, 30)
        text += strings['purge']

    await kick_user(chat_id, user_id)

    msg = await message.reply(text)

    # Del msgs if silent
    if silent:
        to_del = [msg.message_id, message.message_id]
        if 'reply_to_message' in message and message.reply_to_message.from_user.id == user_id:
            to_del.append(message.reply_to_message.message_id)
        await asyncio.sleep(5)
        await tbot.delete_messages(chat_id, to_del)


@register(cmds=['mute', 'smute', 'tmute', 'stmute'], bot_can_restrict_members=True, user_can_restrict_members=True)
@chat_connection(admin=True, only_groups=True)
@get_user_dec()
@get_strings_dec('restrictions')
async def mute_user_cmd(message, chat, user, strings):
    chat_id = chat['chat_id']
    user_id = user['user_id']

    if user_id == BOT_ID:
        await message.reply(strings['mute_sophie'])
        return

    elif user_id == message.from_user.id:
        await message.reply(strings['mute_self'])
        return

    elif await is_user_admin(chat_id, user_id):
        await message.reply(strings['mute_admin'])
        return

    text = strings['user_muted'].format(
        user=await get_user_link(user_id),
        admin=await get_user_link(message.from_user.id),
        chat_name=chat['chat_title']
    )

    curr_cmd = get_cmd(message)

    # Check if temprotary
    until_date = None
    if curr_cmd == 'tmute' or curr_cmd == 'stmute':
        if len(args := message.get_args().split(' ', 2)) > 1:
            try:
                until_date, unit = convert_time(args[1])
            except InvalidTimeUnit:
                await message.reply(strings['invalid_time'])
                return

            text += strings['on_time'] % format_datetime(until_date, locale=strings['language_info']['babel'])

            # Add reason
            if len(args) > 2:
                text += strings['reason'] % args[2]
        else:
            await message.reply(strings['enter_time'])
            return
    else:
        # Add reason
        if len(args := message.get_args().split(' ', 1)) > 1:
            text += strings['reason'] % args[1]

    # Check if silent
    silent = False
    if curr_cmd == 'smute' or curr_cmd == 'stmute':
        silent = True
        key = 'leave_silent:' + str(chat_id)
        redis.set(key, user_id)
        redis.expire(key, 30)
        text += strings['purge']

    await mute_user(chat_id, user_id, until_date=until_date)

    msg = await message.reply(text)

    # Del msgs if silent
    if silent:
        to_del = [msg.message_id, message.message_id]
        if 'reply_to_message' in message and message.reply_to_message.from_user.id == user_id:
            to_del.append(message.reply_to_message.message_id)
        await asyncio.sleep(5)
        await tbot.delete_messages(chat_id, to_del)


@register(f='leave')
async def leave_silent(message):
    if not (user_id := message.from_user.id) == BOT_ID:
        return

    if int(redis.get('leave_silent:' + str(message.chat.id))) == message.left_chat_member.id:
        await message.delete()
