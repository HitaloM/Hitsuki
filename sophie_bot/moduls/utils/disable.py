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

from sophie_bot import OPERATORS
from sophie_bot.services.mongo import db

DISABLABLE_COMMANDS = []


def disablable_dec(command):
    if command not in DISABLABLE_COMMANDS:
        DISABLABLE_COMMANDS.append(command)

    def wrapped(func):
        async def wrapped_1(*args, **kwargs):
            message = args[0]

            chat_id = message.chat.id
            user_id = message.from_user.id

            check = await db.disabled_v2.find_one({'chat_id': chat_id, 'cmds': {'$in': [command]}})
            if check and user_id not in OPERATORS:
                return
            return await func(*args, **kwargs)
        return wrapped_1
    return wrapped
