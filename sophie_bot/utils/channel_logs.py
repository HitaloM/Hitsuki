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

import html

from sophie_bot import bot
from sophie_bot.config import get_int_key
from sophie_bot.utils.logger import log


async def channel_log(msg, info_log=True):
    chat_id = get_int_key('LOGS_CHANNEL_ID')
    if info_log:
        log.info(msg)

    await bot.send_message(chat_id, html.escape(msg))
