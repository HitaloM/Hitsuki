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
from sophie_bot.services.redis import redis


async def prevent_flooding(message, command):
    user_id = message.from_user.id
    if user_id in OPERATORS:
        return True
    key = 'antiflood_{}_{}'.format(user_id, command)
    num = redis.incr(key, 1)
    redis.incr(key, 10)

    if num == 10:
        redis.expire(key, 120)
        await message.reply("Aniflood limit reached, please wait 2 minutes!")
    elif num > 10:
        return False
    return True
