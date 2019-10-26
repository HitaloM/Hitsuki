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

import sys
import asyncio
import hypercorn
# import uvloop

from importlib import import_module

from sophie_bot import dp
from sophie_bot.services.quart import quart
from sophie_bot.utils.logger import log
from sophie_bot.config import get_bool_key
from sophie_bot.moduls import ALL_MODULES, LOADED_MODULES
from sophie_bot.cli import cli


if get_bool_key('LOAD_MODULES'):
    # Import modules
    log.info("Modules to load: %s", str(ALL_MODULES))
    for module_name in ALL_MODULES:
        log.debug("Importing " + module_name)
        imported_module = import_module("sophie_bot.moduls." + module_name)
        LOADED_MODULES.append(imported_module)
    log.info("Modules loaded!")
log.warning("Not importing modules!")


# asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
loop = asyncio.get_event_loop()

# Import misc stuff
import_module("sophie_bot.utils.exit_gracefully")
if not get_bool_key('DEBUG_MODE'):
    import_module("sophie_bot.utils.sentry")


@quart.before_serving
async def startup():
    log.info("Aiogram: Using polling method")
    loop.create_task(dp.start_polling())
    log.info("Bot is alive!")


async def start():
    log.info("Running webserver..")
    config = hypercorn.Config()
    config.bind = ["localhost:8085"]
    await hypercorn.asyncio.serve(quart, config)


if len(sys.argv) > 1:
    cli()


log.info("Starting loop..")
loop.run_until_complete(start())
