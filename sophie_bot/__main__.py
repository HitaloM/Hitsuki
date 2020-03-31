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
from importlib import import_module

import hypercorn
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from sophie_bot import dp
from sophie_bot.config import get_bool_key, get_list_key, get_int_key
from sophie_bot.modules import ALL_MODULES, LOADED_MODULES
from sophie_bot.services.quart import quart
from sophie_bot.utils.logger import log

# import uvloop

if get_bool_key("DEBUG_MODE"):
    log.debug("Enabling logging middleware.")
    dp.middleware.setup(LoggingMiddleware())

LOAD = get_list_key("LOAD")
DONT_LOAD = get_list_key("DONT_LOAD")

if get_bool_key('LOAD_MODULES'):
    if len(LOAD) > 0:
        ALL_MODULES = LOAD

    ALL_MODULES = [x for x in ALL_MODULES if x not in DONT_LOAD]

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

    if not get_bool_key("DEBUG_MODE"):
        log.debug("Waiting 2 seconds...")
        await asyncio.sleep(2)

    log.info("Aiogram: Using polling method")
    loop.create_task(dp.start_polling())
    log.info("Bot is alive!")


async def start():
    log.debug("Running webserver..")
    config = hypercorn.Config()
    port = get_int_key('API_PORT')
    config.bind = [f"localhost:{port}"]
    await hypercorn.asyncio.serve(quart, config)


import_module("sophie_bot.utils.db_structure_migrator")

log.info("Starting loop..")
loop.run_until_complete(start())
