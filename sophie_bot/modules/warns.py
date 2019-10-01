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

import random
import re
import string

from aiogram.types.inline_keyboard import InlineKeyboardMarkup, InlineKeyboardButton

from sophie_bot import WHITELISTED, decorator, mongodb
from sophie_bot.modules.bans import ban_user
from sophie_bot.modules.connections import connection
from sophie_bot.modules.language import get_string, get_strings_dec
from sophie_bot.modules.users import (get_chat_admins, is_user_admin,
                                      user_link, user_admin_dec,
                                      aio_get_user, user_link_html, is_user_premium)


@decorator.command("warn")
@user_admin_dec
@connection(only_in_groups=True, admin=True)
@get_strings_dec("warns")
async def warn_user(message, strings, status, chat_id, chat_title):
    user, reason = await aio_get_user(message)
    if not user:
        return
    user_id = int(user['user_id'])
    if user_id in WHITELISTED:
        await message.reply(strings['usr_whitelist'])
        return
    if user_id in await get_chat_admins(chat_id):
        await message.reply(strings['Admin_no_wrn'])
        return

    rndm = randomString(15)
    mongodb.warns.insert_one({
        'warn_id': rndm,
        'user_id': user_id,
        'group_id': chat_id,
        'reason': str(reason)
    })
    admin_id = message.from_user.id
    admin = mongodb.user_list.find_one({'user_id': admin_id})
    admin_str = await user_link_html(admin['user_id'])
    user_str = await user_link_html(user['user_id'])
    text = strings['warn'].format(admin=admin_str, user=user_str, chat_name=chat_title)
    if reason:
        text += strings['warn_rsn'].format(reason=reason)

    old = mongodb.warns.find({
        'user_id': user_id,
        'group_id': chat_id
    })
    h = 0
    for suka in old:
        h += 1

    buttons = InlineKeyboardMarkup().add(InlineKeyboardButton(
        "⚠️ Remove warn", callback_data='remove_warn_{}'.format(rndm)
    ))
    rules = mongodb.rules.find_one({"chat_id": chat_id})

    if rules:
        buttons.insert(InlineKeyboardButton(
            "📝 Rules", callback_data='get_note_{}_{}'.format(chat_id, rules['note'])
        ))

    if not (db_data := mongodb.warnlimit.find_one({'chat_id': chat_id})):
        warn_limit = 3
    else:
        warn_limit = int(db_data['num'])

    if is_user_premium(user_id):
        warn_limit += 1

    if h >= warn_limit:
        if await ban_user(message, user_id, chat_id, None) is False:
            return
        text += strings['warn_bun'].format(user=user_str)
        mongodb.warns.delete_many({
            'user_id': user_id,
            'group_id': chat_id
        })
    else:
        text += strings['warn_num'].format(curr_warns=h, max_warns=warn_limit)

    await message.reply(text, reply_markup=buttons, disable_web_page_preview=True)


@decorator.CallBackQuery(b'remove_warn_')
async def remove_warn(event):
    user_id = event.query.user_id
    K = await is_user_admin(event.chat_id, user_id)
    if K is False:
        await event.answer(get_string("warns", "rmv_warn_admin", event.chat_id))
        return

    warn_id = re.search(r'remove_warn_(.*)', str(event.data)).group(1)[:-1]
    warn = mongodb.warns.find_one({'warn_id': warn_id})
    if warn:
        mongodb.warns.delete_one({'_id': warn['_id']})
    user_str = await user_link(user_id)
    textx = get_string("warns", "rmv_sfl", event.chat_id)
    await event.edit(textx.format(admin=user_str), link_preview=False)


@decorator.command("warns")
@connection(only_in_groups=True, admin=True)
@get_strings_dec("warns")
async def user_warns(message, strings, status, chat_id, chat_title):
    user, txt = await aio_get_user(message, allow_self=True)
    if not user:
        return

    user_id = int(user['user_id'])
    if user_id in WHITELISTED:
        await message.reply(strings['no_user_warns'].format(user_link_html(user_id)))
        return
    warns = mongodb.warns.find({
        'user_id': user_id,
        'group_id': chat_id
    })
    user_str = await user_link_html(user_id)
    text = strings['warn_list_head'].format(
        user=user_str, chat_name=chat_title)
    number = 0
    for warn in warns:
        number += 1
        reason = warn['reason']
        if not reason or reason == 'None':
            reason = "No reason"
        text += "{}: <code>{}</code>\n".format(number, reason)
    if number == 0:
        await message.reply(strings['user_hasnt_warned'].format(
            user=user_str, chat_name=chat_title))
        return
    await message.reply(text)


@decorator.command("warnlimit")
@user_admin_dec
@connection(only_in_groups=True, admin=True)
@get_strings_dec("warns")
async def warnlimit(message, strings, status, chat_id, chat_title):
    arg = message.get_args()
    if not arg:
        curr = mongodb.warnlimit.find_one({'chat_id': chat_id})
        if curr:
            num = curr['num']
        else:
            num = 3
        await message.reply(strings["warn_limit"].format(chat_name=chat_title, num=num))
    else:
        if int(arg) < 2:
            return await message.reply(strings["warnlimit_too_small"])
        new = {
            'chat_id': chat_id,
            'num': int(arg)
        }
        mongodb.warnlimit.update_one({'chat_id': chat_id}, {"$set": new}, upsert=True)
        await message.reply(strings["warn_limit_upd"].format(arg))


@decorator.command("resetwarns")
@user_admin_dec
@connection(only_in_groups=True, admin=True)
@get_strings_dec("warns")
async def resetwarns(message, strings, status, chat_id, chat_title):
    user, txt = await aio_get_user(message)
    if not user:
        return
    user_id = int(user['user_id'])
    user_str = await user_link_html(user_id)
    check = mongodb.warns.find_one({'group_id': chat_id, 'user_id': user_id})

    if check:
        admin_str = await user_link_html(message.from_user.id)
        purged = mongodb.warns.delete_many({'group_id': chat_id, 'user_id': user_id}).deleted_count
        await message.reply(strings["purged_warns"].format(
            admin=admin_str, user=user_str, number=purged, chat_name=chat_title))
    else:
        await message.reply(strings["usr_no_wrn"].format(user=user_str))


def randomString(stringLength):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for i in range(stringLength))
