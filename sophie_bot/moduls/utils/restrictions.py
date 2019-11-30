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

from aiogram.types.chat_permissions import ChatPermissions

from sophie_bot import bot


async def kick_user(chat_id, user_id):
    await bot.kick_chat_member(chat_id, user_id)
    await bot.unban_chat_member(chat_id, user_id)
    return True


async def mute_user(chat_id, user_id, until_date=None):
    await bot.restrict_chat_member(
        chat_id,
        user_id,
        permissions=ChatPermissions(can_send_messages=False, until_date=until_date),
        until_date=until_date
    )
    return True


async def restrict_user(chat_id, user_id, until_date=None):
    await bot.restrict_chat_member(
        chat_id,
        user_id,
        permissions=ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False,
            until_date=until_date
        ),
        until_date=until_date
    )
    return True


async def unmute_user(chat_id, user_id):
    await bot.restrict_chat_member(
        chat_id,
        user_id,
        can_send_messages=True,
        can_send_media_messages=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True
    )
    return True


async def unban_user(chat_id, user_id):
    await bot.unban_chat_member(chat_id, user_id)
    return True


async def ban_user(chat_id, user_id, until_date=None):
    await bot.kick_chat_member(chat_id, user_id, until_date=until_date)
    return True
