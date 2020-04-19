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
import sys

from sophie_bot import dp, bot
from sophie_bot.services.redis import redis
from sophie_bot.utils.logger import log


@dp.errors_handler()
async def all_errors_handler(message, dp):
    msg = message.callback_query.message if 'callback_query' in message else message.message
    chat_id = msg.chat.id
    err_tlt = sys.exc_info()[0].__name__
    err_msg = str(sys.exc_info()[1])

    if redis.get(chat_id) == err_tlt:
        # by err_tlt we assume that it is same error
        return

    if err_tlt == 'BadRequest' and err_msg == 'Have no rights to send a message':
        return True

    text = "<b>Sorry, I encountered a error!</b>\n"
    text += f'<code>{html.escape(err_tlt)}: {html.escape(err_msg)}</code>'
    redis.set(chat_id, err_tlt, ex=120)
    await bot.send_message(chat_id, text, reply_to_message_id=msg.message_id)

    # Protect Privacy
    msg['chat'] = ['HIDDEN']
    msg['from'] = ['HIDDEN']
    msg['message_id'] = ['HIDDEN']
    if hasattr(msg, 'reply_to_message'):
        msg['reply_to_message'] = ['HIDDEN']

    log.error('Error caused update is: \n' + str(msg))
