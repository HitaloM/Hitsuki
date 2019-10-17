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

check = mongodb.chat_list.find()
F = 0
for chat in check:
    F += 1
    if 'user_id' in chat:
        mongodb.chat_list.delete_one({'_id': chat['_id']})
        print(f"{F} deleted")
