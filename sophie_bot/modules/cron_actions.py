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

import aiocron
import requests
import io
import asyncio
from time import gmtime, strftime

from sophie_bot.modules.sudo_and_owner_stuff import do_backup
from sophie_bot import bot, mongodb
from sophie_bot.config import get_config_key


@aiocron.crontab('47 * * * *')
async def import_cas_bans():
    if get_config_key('sync_cas_bans') is False:
        return
    url = 'https://combot.org/api/cas/export.csv'
    ffile = requests.get(url, allow_redirects=True)
    cas_banned = []
    num = 0
    for user_id in io.StringIO(ffile.text):
        cas_banned.append(user_id[:-2])

    text = f"Start importing <code>{len(cas_banned)}</code> CAS bans"
    if get_config_key('gbans_channel_enabled') is True:
        await bot.send_message(get_config_key('gbans_channel'), text)

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
    if get_config_key('gbans_channel_enabled') is True:
        await bot.send_message(get_config_key('gbans_channel'), text)


@aiocron.crontab('2 * * * *')
async def backup():
    if get_config_key('auto_backups_enabled') is False:
        return
    channel_id = get_config_key('logs_channel_id')
    await do_backup(channel_id)
