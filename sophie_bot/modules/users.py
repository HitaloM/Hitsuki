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

import ujson
import datetime
import html

from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import ChannelParticipantsAdmins

from sophie_bot import OWNER_ID, SUDO, tbot, decorator, logger, redis, db


@decorator.register()
async def msg_handler(message, **kwargs):
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

        await db.chat_list.update_one({'chat_id': chat_id}, {"$set": chat_new}, upsert=True)

        logger.debug(f"Users: Chat {chat_id} updated")

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
    await db.user_list.update_one({'user_id': new_user.id}, {"$set": user_new}, upsert=True)

    logger.debug(f"Users: User {new_user.id} updated")

    return user_new


async def update_admin_cache(chat_id):
    admin_list = await tbot.get_participants(
        int(chat_id), filter=ChannelParticipantsAdmins())
    admins = []
    for admin in admin_list:
        admins.append(admin.id)
    dump = ujson.dumps(admins)
    redis.set('admins_cache_{}'.format(chat_id), dump)
    redis.expire('admins_cache_{}'.format(chat_id), 3600)


async def is_user_admin(chat_id, user_id):
    # User's pm should have admin rights
    if user_id in SUDO:
        return True

    if chat_id == user_id:
        return True

    admins = await get_chat_admins(chat_id)
    if user_id in admins:
        return True
    else:
        return False


async def check_group_admin(event, user_id, no_msg=False):
    if hasattr(event, 'chat_id'):
        chat_id = event.chat_id
    elif hasattr(event, 'chat'):
        chat_id = event.chat.id
    if await is_user_admin(chat_id, user_id) is True:
        return True
    else:
        if no_msg is False:
            await event.reply("You should be a admin to do it!")
        return False


async def get_chat_admins(chat_id):
    dump = redis.get('admins_cache_{}'.format(chat_id))
    if not dump:
        await update_admin_cache(chat_id)
        dump = redis.get('admins_cache_{}'.format(chat_id))

    admins = ujson.decode(dump)
    return admins


async def get_user_and_text(message, send_text=True, allow_self=False):
    args = message.text.split(None, 2)
    user = None
    text = None

    # Only 1 way
    if len(args) < 2 and "reply_to_message" in message:
        user = await get_user_by_id(message.reply_to_message.from_user.id)

    # Get all mention entities
    entities = filter(lambda ent: ent['type'] == 'mention', message.entities)
    for item in entities:
        mention = item.get_text(message.text)

        # Allow get user only in second arg: ex. /warn (user) Reason
        # so if we write nick in reason and try warn by reply it will work as expected
        if mention == args[1]:
            if len(args) > 2:
                text = args[2]
            user = await get_user_by_username(mention)
            if not user:
                await message.answer("I can't get the user!")
                return None, None

    if not user:
        # Ok, now we really be unsure, so don't return right away
        if len(args) > 1:
            if args[1].isdigit():
                user = await get_user_by_id(int(args[1]))

        if len(args) > 2:
            text = args[2]

        # Not first because ex. admins can /warn (user) and reply to offended user
        if not user and "reply_to_message" in message:
            if len(args) > 1:
                text = message.get_args()
            return await get_user_by_id(message.reply_to_message.from_user.id), text

        if not user and allow_self is True:
            user = await get_user_by_id(message.from_user.id)

    if not user:
        if send_text:
            await message.answer("I can't get the user!")
        return None, None

    return user, text


async def get_user_by_username(username):
    # Search username in database
    if '@' in username:
        # Remove '@'
        username = username[1:]

    user = await db.user_list.find_one(
        {'username': username.lower()}
    )

    # Ohnu, we don't have this user in DB
    if not user:
        try:
            user = await add_user_to_db(await tbot(GetFullUserRequest(username)))
        except (ValueError, TypeError):
            user = None

    return user


async def get_user_by_id(user_id: int):
    user = await db.user_list.find_one(
        {'user_id': user_id}
    )
    # Ohnu, we don't have this user in DB
    if not user:
        try:
            user = await add_user_to_db(await tbot(GetFullUserRequest(user_id)))
        except (ValueError, TypeError):
            user = None

    return user


async def add_user_to_db(user):

    if hasattr(user, 'user'):
        user = user.user

    new_user = {
        'user_id': user.id,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'username': user.username
    }

    user = await db.user_list.find_one({'user_id': new_user['user_id']})
    if not user or user is None:
        user = new_user

    if 'chats' not in user:
        new_user['chats'] = []
    if 'user_lang' not in user:
        new_user['user_lang'] = 'en'
        if hasattr(user, 'user_lang'):
            new_user['user_lang'] = user.user_lang

    await db.user_list.update_one(
        {'user_id': user['user_id']},
        {"$set": new_user}, upsert=True
    )

    return new_user


async def get_id_by_nick(data):
    # Check if data is user_id
    user = await db.user_list.find_one({'username': data.replace('@', "")})
    if user:
        return user['user_id']

    user = await tbot(GetFullUserRequest(data))
    return user


async def user_link(user_id):
    user = await get_user_by_id(user_id)
    if user and 'first_name' in user:
        name = user['first_name']
    else:
        name = user_id

    return f"[{name}](tg://user?id={id})"


async def user_link_html(user_id, custom_name=None):
    user = await db.user_list.find_one({'user_id': user_id})
    user_name = None

    if user:
        user_name = user['first_name']
    else:
        try:
            user = await add_user_to_db(await tbot(GetFullUserRequest(int(user_id))))
        except (ValueError, TypeError):
            user_name = str(user_id)

    if custom_name:
        user_name = custom_name

    return "<a href=\"tg://user?id={id}\">{name}</a>".format(name=user_name, id=user_id)


def user_admin_dec(func):
    async def wrapped(event, *args, **kwargs):

        if hasattr(event, 'from_id'):
            user_id = event.from_id
        elif hasattr(event, 'from_user'):
            user_id = event.from_user.id

        if await check_group_admin(event, user_id, no_msg=True) is False:
            await event.reply("You should be admin to do it!")
            return
        return await func(event, *args, **kwargs)
    return wrapped


def user_sudo_dec(func):
    async def wrapped(event):
        if event.from_id not in SUDO:
            return
        return await func(event)
    return wrapped


def user_owner_dec(func):
    async def wrapped(message):
        if not message['from']['id'] == OWNER_ID:
            return
        return await func(message)
    return wrapped


async def is_user_premium(user_id):
    check = await db.premium_users.find_one({'user_id': user_id})
    if check:
        return True
    return False
