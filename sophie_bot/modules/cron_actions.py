import aiocron
import requests
import io
import asyncio
from time import gmtime, strftime

from sophie_bot import CONFIG, bot, mongodb


@aiocron.crontab('50 16 * * *')
async def attime():
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
