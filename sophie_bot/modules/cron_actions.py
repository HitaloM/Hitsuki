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

import aiocron
import requests
import io
import asyncio
from time import gmtime, strftime

from sophie_bot.modules.sudo_and_owner_stuff import do_backup
from sophie_bot import CONFIG, bot, mongodb


@aiocron.crontab('47 * * * *')
async def import_cas_bans():
    if CONFIG['sync_cas_bans'] is False:
        return
    url = 'https://combot.org/api/cas/export.csv'
    ffile = requests.get(url, allow_redirects=True)
    cas_banned = []
    num = 0
    for user_id in io.StringIO(ffile.text):
        cas_banned.append(user_id[:-2])

    text = f"Start importing <code>{len(cas_banned)}</code> CAS bans"
    if CONFIG['advanced']['gbans_channel_enabled'] is True:
        await bot.send_message(CONFIG['advanced']['gbans_channel'], text)

    s_num = 0
    for user_id in cas_banned:
        await asyncio.sleep(0.1)
        num += 1
        print(f"{num}/{len(cas_banned)}")
        gbanned = mongodb.blacklisted_users.find_one({'user': user_id})
        if gbanned:
            print("already gbanned")
            continue

        date = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        new = {
            'user': user_id,
            'date': date,
            'by': "SophieBot import module",
            'reason': "CAS banned"
        }
        mongodb.blacklisted_users.insert_one(new)
        s_num += 1
    text = f"Imported {s_num} CAS bans."
    if CONFIG['advanced']['gbans_channel_enabled'] is True:
        await bot.send_message(CONFIG['advanced']['gbans_channel'], text)


@aiocron.crontab('2 * * * *')
async def backup():
    if CONFIG['advanced']['auto_backups_enabled'] is False:
        return
    channel_id = CONFIG['advanced']['logs_channel_id']
    await do_backup(channel_id)
