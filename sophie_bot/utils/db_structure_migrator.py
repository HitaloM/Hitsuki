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
import time
from importlib import import_module

from sophie_bot import bot, OWNER_ID
from sophie_bot.services.mongo import mongodb
from sophie_bot.utils.logger import log
from sophie_bot.versions import DB_STRUCTURE_VER


async def notify_bot_owner(old_ver, new_ver):
    await bot.send_message(
        OWNER_ID,
        f"Sophie database structure was updated from <code>{old_ver}</code> to <code>{new_ver}</code>"
    )


# TODO: Logs channel


log.debug("Checking on database structure update...")

if not (data := mongodb.db_structure.find_one({'db_ver': {"$exists": True}})):
    log.info("Your database is empty! Creating database structure key...")
    mongodb.db_structure.insert_one({'db_ver': DB_STRUCTURE_VER})
    log.info("Database structure version is: " + str(DB_STRUCTURE_VER))
else:
    curr_ver = data['db_ver']
    log.info("Your database structure version is: " + str(curr_ver))
    if DB_STRUCTURE_VER > curr_ver:
        log.error("Your database is old! Waiting 20 seconds till update...")
        log.info("Press CTRL + C to cancel!")
        time.sleep(20)
        log.debug("Trying to update database structure...")
        log.info("--------------------------------")
        log.info("Your current database structure version: " + str(curr_ver))
        log.info("New database structure version: " + str(DB_STRUCTURE_VER))
        log.info("--------------------------------")
        old_ver = curr_ver
        while curr_ver < DB_STRUCTURE_VER:
            new_ver = curr_ver + 1
            log.info(f"Trying update to {str(new_ver)}...")

            log.debug("Importing: sophie_bot.db." + str(new_ver))
            import_module("sophie_bot.db." + str(new_ver))

            curr_ver += 1
            mongodb.db_structure.update_one({'db_ver': curr_ver - 1}, {"$set": {'db_ver': curr_ver}})

        log.warn(f"Database update done to {str(curr_ver)} successfully!")
        log.debug("Let's notify the bot owner")
        loop = asyncio.get_event_loop()
        bot_info = loop.run_until_complete(notify_bot_owner(old_ver, curr_ver))
        log.info("Rescue normal bot startup...")
    else:
        log.debug("No database structure updates found, skipping!")
