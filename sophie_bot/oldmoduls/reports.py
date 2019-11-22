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

from sophie_bot.modules.connections import connection
from sophie_bot.modules.disable import disablable_dec
from sophie_bot.modules.language import get_strings_dec
from sophie_bot.modules.users import is_user_admin, user_link_html, get_chat_admins, get_user_and_text

from sophie_bot import WHITELISTED, decorator, dp


@dp.message_handler(regexp="^@admin")
@disablable_dec('report')
@connection(only_in_groups=True)
@get_strings_dec('reports')
async def admin_handler(message, strings, *args, **kwargs):
    from_id = message.from_user.id

    if (await is_user_admin(message.chat.id, from_id)) is True:
        return await message.reply(strings['user_user_admin'])

    if from_id in WHITELISTED:
        return await message.reply(strings['user_is_whitelisted'])

    if "reply_to_message" not in message:
        return await message.reply(strings['no_user_to_report'])

    reply_id = message.reply_to_message.from_user.id

    if (await is_user_admin(message.chat.id, reply_id)) is True:
        return await message.reply(strings['report_admin'])

    if reply_id in WHITELISTED:
        return await message.reply(strings['report_whitedlisted'])

    admins = await get_chat_admins(message.chat.id)
    reported = await user_link_html(message.reply_to_message.from_user.id)
    text = strings['reported_user'].format(user=reported)

    try:
        if message.text.split(None, 2)[1]:
            reason = ' '.join(message.text.split(None, 2)[1:])
            text += strings['reported_reason'].format(reason=reason)
    except Exception:
        pass

    for admin in admins:
        text += await user_link_html(admin, custom_name="‏")

    await message.reply(text)


@decorator.register(cmds="report")
@disablable_dec('report')
@connection(only_in_groups=True)
@get_strings_dec('reports')
async def report_user(message, strings, status, chat_id, chat_title):
    from_id = message.from_user.id
    if (await is_user_admin(message.chat.id, from_id)) is True:
        return await message.reply(strings['user_user_admin'])

    if from_id in WHITELISTED:
        return await message.reply(strings['user_is_whitelisted'])

    user, text = await get_user_and_text(message)

    if not user:
        return await message.reply(strings['no_user_to_report'])

    reply_id = user['user_id']

    if (await is_user_admin(message.chat.id, reply_id)) is True:
        return await message.reply(strings['report_admin'])

    if reply_id in WHITELISTED:
        return await message.reply(strings['report_whitedlisted'])

    admins = await get_chat_admins(message.chat.id)
    reported = await user_link_html(user['user_id'])
    msg = strings['reported_user'].format(user=reported)

    if text:
        msg += strings['reported_reason'].format(reason=text)

    for admin in admins:
        msg += await user_link_html(admin, custom_name="‏")

    await message.reply(msg)
