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

import os
import asyncio
import signal
import hypercorn
# import uvloop

from importlib import import_module

from sophie_bot import tbot, redis, logger, dp, quart
from sophie_bot.config import get_config_key
from sophie_bot.modules import ALL_MODULES


LOAD_COMPONENTS = get_config_key("load_components")
CATCH_UP = get_config_key("skip_catch_up")

LOADED_MODULES = []

# Import modules
for module_name in ALL_MODULES:
    logger.debug("Importing " + module_name)
    imported_module = import_module("sophie_bot.modules." + module_name)
    LOADED_MODULES.append(imported_module)

logger.info("Modules loaded!")

if LOAD_COMPONENTS is True:
    from sophie_bot.modules.components import ALL_COMPONENTS

    for module_name in ALL_COMPONENTS:
        logger.debug("Importing " + module_name)
        imported_module = import_module("sophie_bot.modules.components." + module_name)
        LOADED_MODULES.append(imported_module)

    logger.info("Components loaded!")
else:
    logger.info("Components disabled!")


# New asyncio loop
# asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
loop = asyncio.get_event_loop()

# Catch up missed updates
if CATCH_UP is False:
    logger.info("Telethon: Catch up missed updates..")

    try:
        asyncio.ensure_future(tbot.catch_up())
    except Exception as err:
        logger.error(err)


def exit_gracefully(signum, frame):
    logger.info("Bye!")
    try:
        redis.bgsave()
    except Exception:
        logger.info("Exiting immediately!")
    logger.info("----------------------")
    os.kill(os.getpid(), signal.SIGUSR1)


# Signal exit
signal.signal(signal.SIGINT, exit_gracefully)


@quart.before_serving
async def startup():
    logger.info("Aiogram: Using polling method")
    loop.create_task(dp.start_polling())


async def start():
    logger.info("Running webserver..")
    await hypercorn.asyncio.serve(quart, hypercorn.Config())

loop.run_until_complete(start())
