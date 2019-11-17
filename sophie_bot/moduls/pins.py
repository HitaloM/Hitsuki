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

from aiogram.utils.exceptions import BadRequest

from .utils.connections import chat_connection
from .utils.message import get_arg
from .utils.language import get_strings_dec

from sophie_bot.decorator import register
from sophie_bot import bot


@register(cmds="unpin", user_can_pin_messages=True, bot_can_pin_messages=True)
@chat_connection(admin=True, only_in_groups=True)
@get_strings_dec('pins')
async def unpin_message(message, strings, status, chat_id, chat_title):
    try:
        await bot.unpin_chat_message(chat_id)
    except BadRequest:
        await message.reply(strings['chat_not_modified_unpin'])
        return


@register(cmds="pin", user_can_pin_messages=True, bot_can_pin_messages=True)
@get_strings_dec('pins')
async def pin_message(message, strings):
    if 'reply_to_message' not in message:
        await message.reply(strings['no_reply_msg'])
        return
    msg = message.reply_to_message.message_id
    arg = get_arg(message).lower()

    notify = False
    loud = ['loud', 'notify']
    if arg in loud:
        notify = True

    try:
        await bot.pin_chat_message(message.chat.id, msg, disable_notification=notify)
    except BadRequest:
        await message.reply(strings['chat_not_modified_pin'])
