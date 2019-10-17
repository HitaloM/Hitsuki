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

import ujson
import datetime

from sophie_bot import mongodb

load = True

if load is True:
    with open('sophie_bot/update.json', 'r') as f:
        data = ujson.load(f)
        load_type = 'stable'

        for codename in data[load_type]:
            device = data[load_type][codename]

            date_int = int(round(datetime.datetime.strptime(device['modified'], "%Y%m%d%H%M%S").timestamp()))

            new = {
                'codename': codename,
                'fullname': device['fullname'],
                'maintainer': device['maintainer'],
                f'{load_type}_build': device['ver'],
                f'{load_type}_date': date_int,
                f'{load_type}_changelog': device['changelog'],
                f'{load_type}_migrated': True,
            }

            mongodb.ofox_devices.update_one({'codename': codename}, {'$set': new}, upsert=True)
