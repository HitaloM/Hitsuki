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
from telethon.tl.types import ChannelParticipantsAdmins
from telethon.tl.functions.users import GetFullUserRequest

from sophie_bot import OPERATORS

from sophie_bot.services.mongo import db
from sophie_bot.services.telethon import tbot
from sophie_bot.services.redis import redis


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


async def get_user_by_id(user_id: int):
    user = await db.user_list.find_one(
        {'user_id': user_id}
    )
    if not user:
        try:
            user = await add_user_to_db(await tbot(GetFullUserRequest(user_id)))
        except (ValueError, TypeError):
            user = None

    return user


async def get_id_by_nick(data):
    # Check if data is user_id
    user = await db.user_list.find_one({'username': data.replace('@', "")})
    if user:
        return user['user_id']

    user = await tbot(GetFullUserRequest(data))
    return user


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


async def get_user_link(user_id, custom_name=None):
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
    if user_id in OPERATORS:
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


def get_user_and_text_dec(**dec_kwargs):
    def wrapped(func):
        async def wrapped_1(*args, **kwargs):
            message = args[0]
            if hasattr(message, 'message'):
                message = message.message

            user, text = await get_user_and_text(message, **dec_kwargs)
            if not user:
                await message.reply('cant_find_the_user')
                return
            else:
                return await func(*args, user, text, **kwargs)
        return wrapped_1
    return wrapped


def get_user_dec(**dec_kwargs):
    def wrapped(func):
        async def wrapped_1(*args, **kwargs):
            message = args[0]
            if hasattr(message, 'message'):
                message = message.message

            user, text = await get_user_and_text(message, **dec_kwargs)
            if not user:
                await message.reply('cant_find_the_user')
                return
            else:
                return await func(*args, user, **kwargs)
        return wrapped_1
    return wrapped