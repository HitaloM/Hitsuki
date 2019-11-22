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

from sophie_bot.modules.connections import connection
from sophie_bot.modules.users import is_user_admin

from sophie_bot import decorator, mongodb, redis

ALLOWED_LOCKS = (
    'all',
    'text',
)


# Locks processor
@decorator.register()
async def locks_processor(message):
    # Get locks
    chat_id = message.chat.id

    if await is_user_admin(chat_id, message.from_user.id):
        return

    key = 'locks_cache_{}'.format(chat_id)
    locks = None
    if redis.exists(key) > 0:
        locks = redis.lrange(key, 0, -1)
    if not locks:
        if not update_locks_cache(chat_id):
            return
        locks = redis.lrange(key, 0, -1)
    locks = [x.decode('utf-8') for x in locks]

    if 'all' in locks:
        await message.delete()


def update_locks_cache(chat_id):
    key = 'locks_cache_{}'.format(chat_id)
    redis.delete(key)
    data = mongodb.locks.find_one({'chat_id': chat_id})
    if not data:
        return False
    for lock in data:
        if lock == 'chat_id' or lock == '_id':
            continue
        if data[lock] is True:
            redis.lpush(key, lock)
    redis.expire(key, 3600)
    return True


@decorator.register(cmds='locktypes')
async def locktypes_list(message):
    text = "<b>Lock-able items are:</b>\n"
    for item in ALLOWED_LOCKS:
        text += f'* <code>{item}</code>\n'

    await message.reply(text)


@decorator.register(cmds='lock')
@connection(admin=True, only_in_groups=True)
async def lock(message, status, chat_id, chat_title):
    item = message.get_args().lower()
    if item not in ALLOWED_LOCKS:
        await message.reply('You cant lock this!')
        return

    mongodb.locks.update_one({'chat_id': chat_id}, {"$set": {item: True}}, upsert=True)
    update_locks_cache(chat_id)
    await message.reply(f'Locked <code>{item}</code> in <b>{chat_title}</b>!')


@decorator.register(cmds='unlock')
@connection(admin=True, only_in_groups=True)
async def unlock(message, status, chat_id, chat_title):
    item = message.get_args().lower()
    if item not in ALLOWED_LOCKS:
        await message.reply('You cant unlock this!')
        return

    mongodb.locks.update_one({'chat_id': chat_id}, {"$unset": {item: 1}})
    update_locks_cache(chat_id)
    await message.reply(f'Unlocked <code>{item}</code> in <b>{chat_title}</b>!')
