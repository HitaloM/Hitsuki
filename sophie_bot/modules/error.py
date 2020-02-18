# Copyright (C) 2019 The Raphielscape Company LLC.
# Copyright (C) 2018 - 2020 MrYacha
#
# This file is part of SophieBot.
#
# SophieBot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.

import sys
import html

from sophie_bot import dp, bot


@dp.errors_handler()
async def all_errors_handler(message, dp):
    if 'callback_query' in message:
        msg = message.callback_query.message
    else:
        msg = message.message
    chat_id = msg.chat.id
    err_tlt = sys.exc_info()[0].__name__
    err_msg = str(sys.exc_info()[1])

    if err_tlt == 'BadRequest' and err_msg == 'Have no rights to send a message':
        return True

    text = "<b>Sorry, I encountered a error!</b>\n"
    text += f'<code>{html.escape(err_tlt)}: {html.escape(err_msg)}</code>'
    await bot.send_message(chat_id, text, reply_to_message_id=msg.message_id)
