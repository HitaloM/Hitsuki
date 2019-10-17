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
