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

from telethon.errors.rpcerrorlist import UserIsBlockedError, PeerIdInvalidError

from .utils.language import get_strings_dec
from .utils.connections import chat_connection
from .utils.notes import BUTTONS, ALLOWED_COLUMNS, get_parsed_note_list, t_unparse_note_item
from .utils.message import need_args_dec
from sophie_bot.decorator import register
from sophie_bot.services.mongo import db
from sophie_bot.services.redis import redis
from sophie_bot.services.telethon import tbot


@register(cmds=['setrules', 'saverules'], user_admin=True)
@need_args_dec()
@chat_connection(admin=True, only_groups=True)
@get_strings_dec('rules')
async def set_rules(message, chat, strings):
    chat_id = chat['chat_id']

    note = await get_parsed_note_list(message, split_args=0)
    note['chat_id'] = chat_id

    if (await db.rules_v2.replace_one({'chat_id': chat_id}, note, upsert=True)).modified_count > 0:
        text = strings['updated']
    else:
        text = strings['saved']

    await message.reply(text % chat['chat_title'])


@register(cmds='rules')
@chat_connection(only_groups=True)
@get_strings_dec('rules')
async def rules(message, chat, strings):
    chat_id = chat['chat_id']
    send_id = message.chat.id

    if 'reply_to_message' in message:
        rpl_id = message.reply_to_message.message_id
    else:
        rpl_id = message.message_id

    if args := len(message.get_args().split()) > 0:
        arg1 = args[0].lower()
    else:
        arg1 = None
    noformat = True if 'noformat' == arg1 or 'raw' == arg1 else False

    if not (db_item := await db.rules_v2.find_one({'chat_id': chat_id})):
        await message.reply(chat_id, strings['not_found'])
        return

    text, kwargs = await t_unparse_note_item(message, db_item, chat_id, noformat=noformat)
    kwargs['reply_to'] = rpl_id

    await tbot.send_message(send_id, text, **kwargs)


@register(cmds='resetrules', user_admin=True)
@chat_connection(admin=True, only_groups=True)
@get_strings_dec('rules')
async def reset_rules(message, chat, strings):
    chat_id = chat['chat_id']

    if await db.rules_v2.delete_one({'chat_id': chat_id}).deleted_count < 1:
        await message.reply(chat_id, strings['not_found'])
        return

    await message.reply(strings['deleted'])


BUTTONS.update({'rules': 'btn_rules'})


@register(regexp=r'btn_rules:(.*):(\w+)', f='cb', allow_kwargs=True)
@get_strings_dec('rules')
async def rules_btn(event, strings, regexp=None, **kwargs):
    chat_id = int(regexp.group(1))
    user_id = event.from_user.id
    # smthg = regexp.group(2).lower()

    if not (db_item := await db.rules_v2.find_one({'chat_id': chat_id})):
        await event.answer(strings['not_found'])
        return

    text, kwargs = await t_unparse_note_item(event.message, db_item, chat_id, event=event)

    if user_id == event.message.chat.id:
        await event.message.delete()

    try:
        await tbot.send_message(user_id, text, **kwargs)
        await event.answer(strings['rules_was_pmed'])
    except (UserIsBlockedError, PeerIdInvalidError):
        await event.answer(strings['user_blocked'], show_alert=True)
        key = 'btn_rules_start_state:' + str(user_id)
        redis.set(key, chat_id)
        redis.expire(key, 900)


async def __export__(chat_id):
    rules = await db.rules_v2.find_one({'chat_id': chat_id})
    del rules['_id']
    del rules['chat_id']

    return {'rules': rules}


async def __import__(chat_id, data):
    for column in [i for i in data if i not in ALLOWED_COLUMNS]:
        del rules[column]

        rules['chat_id'] = chat_id

    await db.rules_v2.replace_one({'chat_id': rules['chat_id']}, rules, upsert=True)
