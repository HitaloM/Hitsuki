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

from aiogram.types.inline_keyboard import InlineKeyboardMarkup, InlineKeyboardButton
from sophie_bot.modules.users import is_user_admin

from sophie_bot import dp, bot
from sophie_bot.config import get_config_key


@dp.callback_query_handler(regexp='report_error')
async def report_error(query):
    channel_id = get_config_key("errors_channel")
    chat_id = query.message.chat.id
    if await is_user_admin(chat_id, query.from_user.id) is False:
        await query.answer("Only admins can report errors!")
        return
    await bot.forward_message(channel_id, chat_id, query.message.message_id)

    buttons = InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton("Delete message",
                             callback_data='get_delete_msg_{}_admin'.format(chat_id))
    )

    text = "<b>Sorry, I encountered a error!</b>\n"
    text += "Error reported, your report file will be erased in 3 weeks.\n"
    text += "<a href=\"https://t.me/SophieSupport\">Sophie support chat</a>"

    await query.message.edit_caption(
        text,
        reply_markup=buttons
    )

    await query.answer("Error reported! Thank you.")
