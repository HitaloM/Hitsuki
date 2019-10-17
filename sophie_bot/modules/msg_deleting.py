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

from telethon.errors.rpcerrorlist import MessageDeleteForbiddenError

from sophie_bot import decorator, tbot, bot
from sophie_bot.modules.helper_func import bot_rights
from sophie_bot.modules.language import get_strings_dec
from sophie_bot.modules.users import user_admin_dec


@decorator.register(cmds="purge")
@bot_rights.delete_messages()
@user_admin_dec
@get_strings_dec('msg_deleting')
async def purge(message, strings):
    if not message.reply_to_message:
        await message.reply(strings['reply_to_msg'])
        return
    msg_id = message.reply_to_message.message_id
    delete_to = message.message_id

    chat_id = message.chat.id
    msgs = []
    for m_id in range(int(delete_to), msg_id - 1, -1):
        msgs.append(m_id)
        if len(msgs) == 100:
            await tbot.delete_messages(chat_id, msgs)
            msgs = []

    try:
        await tbot.delete_messages(chat_id, msgs)
    except MessageDeleteForbiddenError:
        await message.reply(strings['purge_error'])
        return

    msg = await bot.send_message(chat_id, strings["purge_done"])
    await asyncio.sleep(5)
    await msg.delete()


@decorator.register(cmds="del")
@bot_rights.delete_messages()
@user_admin_dec
@get_strings_dec('msg_deleting')
async def del_message(message, strings):
    if not message.reply_to_message:
        await message.reply(strings['reply_to_msg'])
        return
    msgs = []
    msgs.append(message.message_id)
    msgs.append(message.reply_to_message.message_id)
    await tbot.delete_messages(message.chat.id, msgs)
