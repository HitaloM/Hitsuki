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
