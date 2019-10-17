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

from sophie_bot import mongodb

print(mongodb.blacklisted_users.update_many({'user': {'$exists': True}}, {"$rename": {'user': 'user_id'}}))

print(mongodb.gbanned_groups.update_many({'user': {'$exists': True}}, {"$rename": {'user': 'user_id', 'chat': 'chat_id'}}))