# Copyright (C) 2018 - 2020 MrYacha. All rights reserved. Source code available under the AGPL.
# Copyright (C) 2019 Aiogram
#
# This file is part of Hitsuki (Telegram Bot)
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

from aiogram import executor
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from hitsuki import dp, bot
from hitsuki.config import CONFIG
from hitsuki.modules import ALL_MODULES, LOADED_MODULES, MOD_HELP
from hitsuki.utils.logger import log
from hitsuki.utils import sentry  # need to import to start the service

if CONFIG.debug_mode:
    log.debug("Enabling logging middleware.")
    dp.middleware.setup(LoggingMiddleware())

# Load modules
if len(CONFIG.modules_load) > 0:
    modules = CONFIG.modules_load
else:
    modules = ALL_MODULES

modules = [x for x in modules if x not in CONFIG.modules_not_load]

log.info("Modules to load: %s", str(modules))
for module_name in modules:
    if module_name == 'pm_menu':
        continue
    log.debug(f"Importing <d><n>{module_name}</></>")
    imported_module = import_module("hitsuki.modules." + module_name)
    if hasattr(imported_module, '__help__'):
        if hasattr(imported_module, '__mod_name__'):
            MOD_HELP[imported_module.__mod_name__] = imported_module.__help__
        else:
            MOD_HELP[imported_module.__name__] = imported_module.__help__
    LOADED_MODULES.append(imported_module)
log.info("Modules loaded!")

loop = asyncio.get_event_loop()

import_module('hitsuki.modules.pm_menu')
# Import misc stuff
import_module("hitsuki.utils.exit_gracefully")
if CONFIG.debug_mode:
    import_module("hitsuki.utils.sentry")

async def before_srv_task(loop):
    for module in [m for m in LOADED_MODULES if hasattr(m, '__before_serving__')]:
        log.debug('Before serving: ' + module.__name__)
        loop.create_task(module.__before_serving__(loop))


async def start(_):
    log.debug("Starting before serving task for all modules...")
    loop.create_task(before_srv_task(loop))

    if CONFIG.debug_mode:
        log.debug("Waiting 2 seconds...")
        await asyncio.sleep(2)


async def start_webhooks(_):
    await bot.set_webhook(CONFIG.webhooks_url + f"/{CONFIG.token}")
    return await start(_)


log.info("Starting loop..")
log.info("Aiogram: Using polling method")

if CONFIG.webhooks_enable:
    executor.start_webhook(dp, f'/{CONFIG.token}', on_startup=start_webhooks, port=CONFIG.webhooks_port)
else:
    executor.start_polling(dp, loop=loop, on_startup=start)
