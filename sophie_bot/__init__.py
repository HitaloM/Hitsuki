# Copyright (C) 2018 - 2020 MrYacha. All rights reserved. Source code available under the AGPL.
# Copyright (C) 2019 Aiogram
#
# This file is part of SophieBot.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.bot.api import TelegramAPIServer, TELEGRAM_PRODUCTION
from aiogram.contrib.fsm_storage.redis import RedisStorage2

from sophie_bot.config import CONFIG
from sophie_bot.utils.logger import log
from sophie_bot.versions import SOPHIE_VERSION

log.info("----------------------")
log.info("|      SophieBot     |")
log.info("----------------------")
log.info("Version: " + SOPHIE_VERSION)

if CONFIG.debug_mode:
    SOPHIE_VERSION += "-debug"
    log.setLevel(logging.DEBUG)
    log.warn("! Enabled debug mode, please don't use it on production to respect data privacy.")

# Support for custom BotAPI servers
bot_api = TelegramAPIServer.from_base(CONFIG.botapi_server) if CONFIG.botapi_server else TELEGRAM_PRODUCTION

# AIOGram
bot = Bot(token=CONFIG.token, parse_mode=types.ParseMode.HTML, server=bot_api)
storage = RedisStorage2(
    host=CONFIG.redis_host,
    port=CONFIG.redis_port,
    db=CONFIG.redis_db_states
)
dp = Dispatcher(bot, storage=storage)

loop = asyncio.get_event_loop()

log.debug("Getting bot info...")
bot_info = loop.run_until_complete(bot.get_me())
BOT_USERNAME = bot_info.username
BOT_ID = bot_info.id
