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

import re
from time import gmtime, strftime

from sophie_bot import mongodb, logger

f = open("owo.txt").read()
F = 0
L = round(sum(1 for line in open("owo.txt")) / 2)


oof = re.findall("\[x\] ?(.+) - (\d+)\nReason: (.*)", f, re.MULTILINE)
for user in oof:
    F += 1
    name = user[0]
    user_id = user[1]
    reason = user[2]

    logger.info(f"{F}/~{L} - Gbanning {name} - {user_id}")

    date = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    new = {
        'user': user_id,
        'date': date,
        'by': "SophieBot import module",
        'reason': reason
    }
    old = mongodb.blacklisted_users.find_one({'user': user_id})
    if old:
        logger.info(f"User {user_id} already gbanned, ill update the reason")
        mongodb.blacklisted_users.update_one({'_id': old['_id']}, {"$set": new}, upsert=False)
    else:
        mongodb.blacklisted_users.insert_one(new)
        logger.info(f"User {user_id} gbanned!")
