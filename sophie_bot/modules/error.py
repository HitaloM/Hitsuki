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

from redis.exceptions import RedisError

from sophie_bot import dp, bot, OWNER_ID
from sophie_bot.services.redis import redis
from sophie_bot.utils.logger import log

SENT = []


def catch_redis_error(**dec_kwargs):
    def wrapped(func):
        async def wrapped_1(*args, **kwargs):
            global SENT
            # We can't use redis here
            # So we save data - 'message sent to' in a list variable
            message = args[0]
            msg = message.callback_query.message if 'callback_query' in message else message.message
            chat_id = msg.chat.id
            try:
                return await func(*args, **kwargs)
            except RedisError:
                if chat_id not in SENT:
                    text = 'Sorry for inconvience! I encountered error in my redis DB, which is necessary for running '\
                           'bot \n\nPlease report this to my support group immediately when you see this error!'
                    if await bot.send_message(chat_id, text):
                        SENT.append(chat_id)
                # Alert bot owner
                if OWNER_ID not in SENT:
                    text = 'Sophie panic: Got redis error'
                    if await bot.send_message(OWNER_ID, text):
                        SENT.append(OWNER_ID)
                log.error(RedisError, exc_info=True)
                return False
        return wrapped_1
    return wrapped


@dp.errors_handler()
@catch_redis_error()
async def all_errors_handler(message, error):
    msg = message.callback_query.message if 'callback_query' in message else message.message
    chat_id = msg.chat.id
    reply_to = msg.message_id
    err_tlt = sys.exc_info()[0].__name__
    err_msg = str(sys.exc_info()[1])

    log.warn('Error caused update is: \n' + str(parse_update(message)))

    if redis.get(chat_id) == str(error):
        # by err_tlt we assume that it is same error
        return

    if err_tlt == 'BadRequest' and err_msg == 'Have no rights to send a message':
        return True

    text = "<b>Sorry, I encountered a error!</b>\n"
    text += f'<code>{html.escape(err_tlt)}: {html.escape(err_msg)}</code>'
    redis.set(chat_id, str(error), ex=600)
    await bot.send_message(chat_id, text, reply_to_message_id=reply_to)


def parse_update(update):
    # The parser to hide sensitive informations in the update (for logging)
    update = (update['callback_query']['message'] if 'callback_query' in update else
              update['message'] if hasattr(update, 'message') else update)

    if 'chat' in update:
        chat = update['chat']
        chat['id'] = chat['title'] = chat['username'] = chat['first_name'] = chat['last_name'] = []
    if user := update['from']:
        user['id'] = user['first_name'] = user['last_name'] = user['username'] = []
    if 'reply_to_message' in update:
        reply_msg = update['reply_to_message']
        reply_msg['chat']['id'] = reply_msg['chat']['title'] = reply_msg['chat']['first_name'] = \
            reply_msg['chat']['last_name'] = reply_msg['chat']['username'] = []
        reply_msg['from']['id'] = reply_msg['from']['first_name'] = reply_msg['from']['last_name'] = \
            reply_msg['from']['username'] = []
        reply_msg['message_id'] = []
        reply_msg['new_chat_members'] = reply_msg['left_chat_member'] = []
    update['new_chat_members'] = update['left_chat_member'] = []
    update['message_id'] = []
    return update
