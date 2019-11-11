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
import time
import os
from importlib import import_module

from sophie_bot.utils.logger import log
from sophie_bot.services.mongo import mongodb
from sophie_bot.versions import DB_STRUCTURE_VER
from sophie_bot import bot, OWNER_ID


async def notify_bot_owner(old_ver, new_ver):
    await bot.send_message(
        OWNER_ID,
        f"Sophie database structure was updated from <code>{old_ver}</code> to <code>{new_ver}</code>"
    )
    # TODO: Logs channel


log.info("Checking on database structure update...")

if not (data := mongodb.db_structure.find_one({'db_ver': {"$exists": True}})):
    log.warning("Your database is empty! Creating database structure key...")
    mongodb.db_structure.insert_one({'db_ver': DB_STRUCTURE_VER})
    log.warning("Your database structure version is: " + str(DB_STRUCTURE_VER))
else:
    curr_ver = data['db_ver']
    log.info("Your database structure version is: " + str(curr_ver))
    if DB_STRUCTURE_VER > curr_ver:
        log.critical("Your database is old! Waiting 10 seconds till update...")
        log.warn("Press CTRL + C to cancel!")
        time.sleep(10)
        log.error("Trying to update database structure...")
        log.warn("--------------------------------")
        log.warn("Your current database structure version: " + str(curr_ver))
        log.warn("New database structure version: " + str(DB_STRUCTURE_VER))
        log.warn("--------------------------------")
        old_ver = curr_ver
        while curr_ver < DB_STRUCTURE_VER:
            new_ver = curr_ver + 1
            log.warn(f"Trying update to {str(new_ver)}...")

            log.debug("Importing: sophie_bot.db." + str(new_ver))
            import_module("sophie_bot.db." + str(new_ver))

            curr_ver += 1
            mongodb.db_structure.update_one({'db_ver': curr_ver - 1}, {"$set": {'db_ver': curr_ver}})

        log.error(f"Database update done to {str(curr_ver)} successfully")
        log.debug("Let's notify the bot owner")
        loop = asyncio.get_event_loop()
        bot_info = loop.run_until_complete(notify_bot_owner(old_ver, curr_ver))
        log.warn("Rescue normal bot startup...")
    else:
        log.info("No database structure updates found, skipping!")
