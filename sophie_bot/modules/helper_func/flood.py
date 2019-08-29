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

from sophie_bot import SUDO, redis


async def prevent_flooding(message, command):
    user_id = message.from_user.id
    if user_id in SUDO:
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
