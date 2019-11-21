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

import redis
from redisworks import Root
from sophie_bot.config import get_str_key, get_int_key


# Init Redis
redis = redis.StrictRedis(
    host=get_str_key("REDIS_HOST"),
    port=get_str_key("REDIS_PORT"),
    db=get_int_key("REDIS_DB_FSM"),
    decode_responses=True
)

rw = Root()
