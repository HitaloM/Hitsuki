# Copyright © 2018, 2019 MrYacha
# This file is part of SophieBot.
#
# SophieBot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SophieBot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License

import sys
import io
import traceback
import ujson
import datetime
import random

from time import gmtime, strftime

from aiogram import types

from aiogram.types.inline_keyboard import InlineKeyboardMarkup, InlineKeyboardButton

from sophie_bot import DEBUG_MODE, mongodb, dp, logger, bot
from sophie_bot.modules.helper_func.term import term
from sophie_bot.config import get_config_key


RANDOM_ERROR_TITLES = [
    "IT'S A CREEEPER!!!1",
    "BOOM!",
    "It was funny, I go away.",
    "Don't look at me 😒",
    "Someone again messed me",
    ":( Your PC ran into a problem and needs to restart...",
    "Hello Microsoft?",
    "YEY NEW ERROR! Lets spam to developers.",
    "It's hurt me",
    "I'm crashed, but you still can use /cat command",
    "PIX ME SOME1 PLOX",
    "*Blue screen of death*",
    "It's crash time!"
]


@dp.errors_handler()
async def all_errors_handler(message, dp):
    await report_error(message)


async def report_error(event, telethon=False):
    error = str(sys.exc_info()[1])
    class_error = sys.exc_info()[0].__name__

    if class_error == 'ChatWriteForbiddenError':
        # This error mean bot is muted in chat
        return
    elif class_error == 'BadRequest' and error == 'Have no rights to send a message':
        return
    elif class_error == 'RetryAfter':
        return

    if telethon:
        msg = event
        chat_id = msg.chat_id
        lib = 'Telethon'
    else:
        lib = 'Aiogram'
        if 'callback_query' in event:
            msg = event.callback_query.message
        else:
            msg = event.message
        chat_id = msg.chat.id

    date = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    logger.error("Error: " + date)
    logger.error("Lib: " + lib)

    if telethon:
        logger.error(traceback.format_exc())

    if DEBUG_MODE:
        await msg.reply(error)
        return

    new = {
        'error_class_name': class_error,
        'error': error,
        'date': datetime.datetime.now()
    }
    mongodb.errors.insert_one(new)

    # text = "<b>Sorry, I encountered a error!</b>\n"
    text = random.choice(RANDOM_ERROR_TITLES)
    text += "\n<a href=\"https://t.me/SophieSupport\">Sophie support chat</a>"

    ftext = "Sophie error log file."
    ftext += "\n______________________\n"
    ftext += "\nIf you wanna you can report it - just press the \"Report error\" button."
    ftext += "\nTill you press report button your data will be only here."
    ftext += "\n______________________\n"
    ftext += "\nDate: " + date
    ftext += "\nLib: " + lib
    ftext += "\nGroup ID: " + str(chat_id)
    ftext += "\nSender ID: " + str(msg.from_user.id if lib == "Aiogram" else msg.from_id)
    ftext += "\nText: " + str(msg.text or "")
    ftext += "\n\nRaw update text:\n"
    ftext += str(event)
    ftext += "\n\nTraceback info:\n"
    ftext += str(traceback.format_exc())
    ftext += "\n\nFormatted update text:\n"
    ftext += str(ujson.dumps(msg, indent=2))

    command = "git log --pretty=format:\"%an: %s\" -5"
    ftext += "\n\n\nLast 5 commits:\n"
    ftext += await term(command)

    buttons = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("Delete message",
                             callback_data='get_delete_msg_{}_admin'.format(chat_id))
    )

    if get_config_key("errors_channel_enabled"):
        buttons.insert(InlineKeyboardButton("Report crash", callback_data='report_error'))

    await bot.send_document(
        chat_id,
        types.InputFile(io.StringIO(ftext), filename="CrashReport.txt"),
        caption=text,
        reply_to_message_id=msg.message_id if lib == "Aiogram" else msg.message.id,
        reply_markup=buttons
    )

    return
