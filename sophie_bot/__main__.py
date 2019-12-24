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

import asyncio
from importlib import import_module
from aiogram.contrib.middlewares.logging import LoggingMiddleware

import hypercorn

from sophie_bot import dp
from sophie_bot.config import get_bool_key
from sophie_bot.modules import ALL_MODULES, LOADED_MODULES
from sophie_bot.services.quart import quart
from sophie_bot.utils.db_backup import backup_db
from sophie_bot.utils.logger import log

# import uvloop

if get_bool_key("DEBUG_MODE") is True:
    log.debug("Enabling logging middleware.")
    dp.middleware.setup(LoggingMiddleware())


if get_bool_key('LOAD_MODULES'):
    # Import modules
    log.info("Modules to load: %s", str(ALL_MODULES))
    for module_name in ALL_MODULES:
        log.debug(f"Importing <d><n>{module_name}</></>")
        imported_module = import_module("sophie_bot.modules." + module_name)
        LOADED_MODULES.append(imported_module)
    log.info("Modules loaded!")
else:
    log.warning("Not importing modules!")


# asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
loop = asyncio.get_event_loop()

# Import misc stuff
import_module("sophie_bot.utils.exit_gracefully")
if not get_bool_key('DEBUG_MODE'):
    import_module("sophie_bot.utils.sentry")


async def before_srv_task(loop):
    for module in [m for m in LOADED_MODULES if hasattr(m, '__before_serving__')]:
        log.debug('Before serving: ' + module.__name__)
        loop.create_task(module.__before_serving__(loop))


@quart.before_serving
async def startup():
    log.debug("Starting before serving task for all modules...")
    loop.create_task(before_srv_task(loop))

    log.debug("Waiting 2 seconds...")
    await asyncio.sleep(2)

    log.info("Aiogram: Using polling method")
    loop.create_task(dp.start_polling())
    log.info("Bot is alive!")


async def start():
    log.debug("Running webserver..")
    config = hypercorn.Config()
    config.bind = ["localhost:8085"]
    await hypercorn.asyncio.serve(quart, config)


if get_bool_key('BACKUP_DB_ON_STARTUP'):
    backup_db()


import_module("sophie_bot.utils.db_structure_migrator")


log.info("Starting loop..")
loop.run_until_complete(start())
