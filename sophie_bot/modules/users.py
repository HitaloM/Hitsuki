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

import datetime
import html

from sophie_bot.decorator import register
from sophie_bot.modules import LOADED_MODULES
from sophie_bot.services.mongo import db
from sophie_bot.utils.logger import log
from .utils.connections import chat_connection
from .utils.disable import disableable_dec
from .utils.language import get_strings_dec
from .utils.user_details import get_user_dec, get_user_link, is_user_admin, get_admins_rights


@register()
async def update_users_handler(message):
    chat_id = message.chat.id

    # Update chat
    new_chat = message.chat
    if not new_chat.type == 'private':

        old_chat = await db.chat_list.find_one({'chat_id': chat_id})

        if not hasattr(new_chat, 'username'):
            chatnick = None
        else:
            chatnick = new_chat.username

        if old_chat and 'first_detected_date' in old_chat:
            first_detected_date = old_chat['first_detected_date']
        else:
            first_detected_date = datetime.datetime.now()

        chat_new = {
            "chat_id": chat_id,
            "chat_title": html.escape(new_chat.title),
            "chat_nick": chatnick,
            "type": new_chat.type,
            "first_detected_date": first_detected_date
        }

        # Check on old chat in DB with same username
        find_old_chat = {
            'chat_nick': chat_new['chat_nick'],
            'chat_id': {'$ne': chat_new['chat_id']}
        }
        if chat_new['chat_nick'] and (check := await db.chat_list.find_one(find_old_chat)):
            await db.chat_list.delete_one({'_id': check['_id']})
            log.info(
                f"Found chat ({check['chat_id']}) with same username as ({chat_new['chat_id']}), old chat was deleted.")

        await db.chat_list.update_one({'chat_id': chat_id}, {"$set": chat_new}, upsert=True)

        log.debug(f"Users: Chat {chat_id} updated")

    # Update users
    await update_user(chat_id, message.from_user)

    if "reply_to_message" in message and \
            hasattr(message.reply_to_message.from_user, 'chat_id') and \
            message.reply_to_message.from_user.chat_id:
        await update_user(chat_id, message.reply_to_message.from_user)

    if "forward_from" in message:
        await update_user(chat_id, message.forward_from)


async def update_user(chat_id, new_user):
    old_user = await db.user_list.find_one({'user_id': new_user.id})

    new_chat = [chat_id]

    if old_user and 'chats' in old_user:
        if old_user['chats']:
            new_chat = old_user['chats']
        if not new_chat or chat_id not in new_chat:
            new_chat.append(chat_id)

    if old_user and 'first_detected_date' in old_user:
        first_detected_date = old_user['first_detected_date']
    else:
        first_detected_date = datetime.datetime.now()

    if new_user.username:
        username = new_user.username.lower()
    else:
        username = None

    if hasattr(new_user, 'last_name') and new_user.last_name:
        last_name = html.escape(new_user.last_name)
    else:
        last_name = None

    first_name = html.escape(new_user.first_name)

    user_new = {
        'user_id': new_user.id,
        'first_name': first_name,
        'last_name': last_name,
        'username': username,
        'user_lang': new_user.language_code,
        'chats': new_chat,
        'first_detected_date': first_detected_date
    }

    # Check on old user in DB with same username
    find_old_user = {
        'username': user_new['username'],
        'user_id': {'$ne': user_new['user_id']}
    }
    if user_new['username'] and (check := await db.user_list.find_one(find_old_user)):
        await db.user_list.delete_one({'_id': check['_id']})
        log.info(
            f"Found user ({check['user_id']}) with same username as ({user_new['user_id']}), old user was deleted.")

    await db.user_list.update_one({'user_id': new_user.id}, {"$set": user_new}, upsert=True)

    log.debug(f"Users: User {new_user.id} updated")

    return user_new


@register(cmds="info")
@disableable_dec("info")
@get_user_dec(allow_self=True)
@get_strings_dec("users")
async def user_info(message, user, strings):
    chat_id = message.chat.id

    text = strings["user_info"]
    text += strings["info_id"].format(id=user['user_id'])
    text += strings["info_first"].format(first_name=str(user['first_name']))

    if user['last_name'] is not None:
        text += strings["info_last"].format(last_name=str(user['last_name']))

    if user['username'] is not None:
        text += strings["info_username"].format(username="@" + str(user['username']))

    text += strings['info_link'].format(user_link=str(await get_user_link(user['user_id'])))

    text += '\n'

    if await is_user_admin(chat_id, user['user_id']) is True:
        text += strings['info_admeme']

    for module in [m for m in LOADED_MODULES if hasattr(m, '__user_info__')]:
        if txt := await module.__user_info__(message, user['user_id']):
            text += txt

    text += strings['info_saw'].format(num=len(user['chats']))

    await message.reply(text)


@register(cmds="admincache", is_admin=True)
@chat_connection(only_groups=True, admin=True)
@get_strings_dec("users")
async def reset_admins_cache(message, chat, strings):
    await get_admins_rights(chat['chat_id'], force_update=True)  # Reset a cache
    await message.reply(strings['upd_cache_done'])


@register(cmds=["adminlist", "admins"])
@disableable_dec("adminlist")
@chat_connection(only_groups=True)
@get_strings_dec("users")
async def adminlist(message, chat, strings):
    admins = await get_admins_rights(chat['chat_id'])
    text = strings['admins']
    for admin in admins:
        if user := await db.user_list.find_one({'user_id': admin}):
            text += '- {} ({})\n'.format(await get_user_link(user['user_id']), user['user_id'])

    await message.reply(text)


async def __stats__():
    text = "* <code>{}</code> total users, in <code>{}</code> chats\n".format(
        await db.user_list.count_documents({}),
        await db.chat_list.count_documents({})
    )

    text += "* <code>{}</code> new users and <code>{}</code> new chats in the last 48 hours\n".format(
        await db.user_list.count_documents({
            'first_detected_date': {'$gte': datetime.datetime.now() - datetime.timedelta(days=2)}
        }),
        await db.chat_list.count_documents({
            'first_detected_date': {'$gte': datetime.datetime.now() - datetime.timedelta(days=2)}
        })
    )

    return text
