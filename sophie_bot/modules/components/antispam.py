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

import requests

from nostril import nonsense

from sophie_bot import CONFIG, decorator, tbot, mongodb
from telethon.tl.functions.photos import GetUserPhotosRequest
from sophie_bot.modules.users import aio_get_user, user_link_html


NAMES = []
COUNTRY_EMOJIS = '🇦🇨🇦🇩🇦🇪🇦🇫🇦🇬🇦🇮🇦🇱🇦🇲🇦🇴🇦🇶🇦🇷🇦🇸🇦🇹🇦🇺🇦🇼🇦🇽🇦🇿🇧🇦🇧🇧🇧🇩🇧🇪🇧🇫🇧🇬🇧🇭🇧🇮🇧🇯🇧🇱🇧🇲🇧🇳🇧🇴🇧🇶🇧🇷🇧🇸🇧🇹🇧🇻🇧🇼🇧🇾🇧🇿🇨🇦🇨🇨🇨🇩🇨🇫🇨🇬🇨🇭🇨🇮🇨🇰🇨🇱🇨🇲🇨🇳🇨🇴🇨🇵🇨🇷🇨🇺🇨🇻🇨🇼🇨🇽🇨🇾🇨🇿🇩🇪🇩🇬🇩🇯🇩🇰🇩🇲🇩🇴🇩🇿🇪🇦🇪🇨🇪🇪🇪🇬🇪🇭🇪🇷🇪🇸🇪🇹🇪🇺🇫🇮🇫🇯🇫🇰🇫🇲🇫🇴🇫🇷🇬🇦🇬🇧🇬🇩🇬🇪🇬🇫🇬🇬🇬🇭🇬🇮🇬🇱🇬🇲🇬🇳🇬🇵🇬🇶🇬🇷🇬🇸🇬🇹🇬🇺🇬🇼🇬🇾🇭🇰🇭🇲🇭🇳🇭🇷🇭🇹🇭🇺🇮🇨🇮🇩🇮🇪🇮🇱🇮🇲🇮🇳🇮🇴🇮🇶🇮🇷🇮🇸🇮🇹🇯🇪🇯🇲🇯🇴🇯🇵🇰🇪🇰🇬🇰🇭🇰🇮🇰🇲🇰🇳🇰🇵🇰🇷🇰🇼🇰🇾🇰🇿🇱🇦🇱🇧🇱🇨🇱🇮🇱🇰🇱🇷🇱🇸🇱🇹🇱🇺🇱🇻🇱🇾🇲🇦🇲🇨🇲🇩🇲🇪🇲🇫🇲🇬🇲🇭🇲🇰🇲🇱🇲🇲🇲🇳🇲🇴🇲🇵🇲🇶🇲🇷🇲🇸🇲🇹🇲🇺🇲🇻🇲🇼🇲🇽🇲🇾🇲🇿🇳🇦🇳🇨🇳🇪🇳🇫🇳🇬🇳🇮🇳🇱🇳🇴🇳🇵🇳🇷🇳🇺🇳🇿🇴🇲🇵🇦🇵🇪🇵🇫🇵🇬🇵🇭🇵🇰🇵🇱🇵🇲🇵🇳🇵🇷🇵🇸🇵🇹🇵🇼🇵🇾🇶🇦🇷🇪🇷🇴🇷🇸🇷🇺🇷🇼🇸🇦🇸🇧🇸🇨🇸🇩🇸🇪🇸🇬🇸🇭🇸🇮🇸🇯🇸🇰🇸🇱🇸🇲🇸🇳🇸🇴🇸🇷🇸🇸🇸🇹🇸🇻🇸🇽🇸🇾🇸🇿🇹🇦🇹🇨🇹🇩🇹🇫🇹🇬🇹🇭🇹🇯🇹🇰🇹🇱🇹🇲🇹🇳🇹🇴🇹🇷🇹🇹🇹🇻🇹🇼🇹🇿🇺🇦🇺🇬🇺🇲🇺🇳🇺🇸🇺🇾🇺🇿🇻🇦🇻🇨🇻🇪🇻🇬🇻🇮🇻🇳🇻🇺🇼🇫🇼🇸🇽🇰🇾🇪🇾🇹🇿🇦🇿🇲🇿🇼🏴󠁧󠁢󠁥󠁮󠁧󠁿🏴󠁧󠁢󠁳󠁣󠁴󠁿'

# Testing module

#with open('sophie_bot/names.txt') as f:
#    for line in f:
#        NAMES.append(line.lower().replace('\n', ''))


@decorator.command('checkspammer', is_sudo=True)
async def check_manually(message):
    # This command used to test new antispammers AI functions
    user, txt = await aio_get_user(message, allow_self=True)
    if not user:
        return

    user_id = user['user_id']

    name = user['first_name']
    user_pics = await tbot(GetUserPhotosRequest(
        int(user['user_id']),
        offset=0,
        max_id=0,
        limit=100))

    if user['last_name']:
        name += user['last_name']

    num = 0

    text = "User " + await user_link_html(user['user_id'])
    text += "\nName: " + name
    text += "\nID: <code>" + str(user['user_id']) + '</code>'

    text += '\n'

    gbanned = mongodb.blacklisted_users.find_one({'user': user_id})
    if gbanned:
        text += "\n<b>Warn! User gbanned in SophieBot!</b>"
        text += f"\nDate: <code>{gbanned['date']}</code>"
        text += f"\nReason: <code>{gbanned['reason']}</code>"
        text += '\n'
        num += 999
    else:
        text += "\nUser not gbanned in SophieBot"

    api_url = "https://api.unifiedban.solutions/blacklist/check/" + str(user_id)

    ubanned = requests.get(api_url, headers={'Authorization': CONFIG['advanced']['utoken']})

    if ubanned.text == '{"Error": "No data"}':
        text += "\nUser not ubanned."

    if user['first_name'].replace(' ', '').isdigit():
        text += "\n<b>Warn! User have name with only numbers!</b>"
        num += 80

    if user['first_name'].lower() in NAMES:
        text += "\n<b>Warn! User have real name (Mostly spammers try to be like real human)!</b>"
        num += 75

    if user_pics and len(user_pics.photos) == 1:
        text += "\n<b>Warn! User have only 1 display picture!</b>"
        num += 40
    if user_pics and len(user_pics.photos) == 0:
        text += "\n<b>Warn! User don't have any DP!</b>"
        num += 25

    try:
        check = nonsense(name)
        if check is True:
            text += "\n<b>Warn! User have noncence name!</b>"
            num += 85
        else:
            text += "\nUser have normal name"
    except ValueError:
        text += "\nName too short to analyse it"

    # Counterweight
    if '#' in name:
        text += "\nUser have hashtag in name, mostly only real users have it"
        num -= 20

    if "☭" in name:
        text += "\nGood soveit boi."
        num -= 20

    if "🌈" in name:
        text += "\nGei detected."
        num -= 20

    if "🦊" in name:
        text += "\nHa, this guy is a fox lover."
        num -= 20

    for owo in COUNTRY_EMOJIS:
        if owo in name:
            text += "\nHa, This guy love own country"
            num -= 20
            break
    #

    text += "\n\nDebug: Real suspicion numer: " + str(num)

    if num > 100:
        num = 100

    if num < 0:
        num = 0

    text += '\n\n<b>Suspicion: </b><code>' + str(num) + "%</code>"

    await message.reply(str(text))
