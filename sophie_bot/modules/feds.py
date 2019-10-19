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

import asyncio
import datetime
import io
import uuid

import ujson
from aiogram import types
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import ChannelParticipantCreator

from sophie_bot import SOPHIE_VERSION, OWNER_ID, BOT_ID, WHITELISTED, tbot, decorator, mongodb, bot, db
from sophie_bot.modules.connections import connection, get_conn_chat
from sophie_bot.modules.language import get_string, get_strings_dec
from sophie_bot.modules.users import is_user_admin, get_user_and_text, user_link_html


def get_user_and_fed_and_text_dec(func):
    async def wrapped_1(message, *args, **kwargs):
        user, text = await get_user_and_text(message)
        if not user:
            return

        status, chat_id, chat_title = await get_conn_chat(
            message.from_user.id, message.chat.id)

        fed = None

        if text:
            text_args = text.split(" ", 1)

            if len(text_args) >= 1:
                if text_args[0].count('-') == 4:
                    if len(text_args) > 1:
                        text = text_args[1]
                    else:
                        text = ""
                    fed = await db.feds.find_one({'fed_id': text_args[0]})
                    if not fed:
                        await message.reply(get_string("feds", 'fed_id_invalid', message.chat.id))
                        return
                else:
                    text = " ".join(text_args)

        if not fed:
            fed = await db.feds.find_one({'chats': {'$in': [chat_id]}})
            if not fed:
                await message.reply(get_string("feds", 'chat_not_in_fed', message.chat.id))
                return

        return await func(message, user, fed, text, *args, **kwargs)
    return wrapped_1


def get_fed_dec(func):
    async def wrapped_1(message, *args, **kwargs):
        fed = None

        status, chat_id, chat_title = await get_conn_chat(
            message.from_user.id, message.chat.id)

        text_args = message.text.split(" ", 1)
        if not len(text_args) < 2:
            if text_args[1].count('-') == 4:
                fed = await db.feds.find_one({'fed_id': text_args[1]})
                if not fed:
                    await message.reply(get_string("feds", 'fed_id_invalid', message.chat.id))
                    return

        if not fed:
            fed = await db.feds.find_one({'chats': {'$in': [chat_id]}})
            if not fed:
                await message.reply(get_string("feds", 'chat_not_in_fed', message.chat.id))
                return

        return await func(message, fed, *args, **kwargs)
    return wrapped_1


def user_is_fed_admin(func):
    async def wrapped_1(message, *args, **kwargs):
        user_id = message.from_user.id
        real_chat_id = message.chat.id

        if user_id == OWNER_ID:
            return await func(message, *args, **kwargs)

        status, chat_id, chat_title = await get_conn_chat(
            user_id, real_chat_id, only_in_groups=True)

        fed = await db.feds.find_one({'chats': {'$in': [chat_id]}})
        if not fed:
            await message.reply(get_string("feds", 'chat_not_in_fed', real_chat_id))
            return False
        if not user_id == fed['creator']:
            if user_id not in fed['admins']:
                await message.reply(get_string("feds", 'need_admin_to_fban', real_chat_id).format(
                    name=fed['fed_name']))
        return await func(message, *args, **kwargs)
    return wrapped_1


# Commands


@decorator.register(cmds='newfed')
@get_strings_dec("feds")
async def new_fed(message, strings, **kwargs):
    fed_name = message.get_args()
    user_id = message.from_user.id
    if not fed_name:
        await message.reply(strings['no_args'])

    if len(fed_name) > 60:
        await message.reply(strings['fed_name_long'])
        return

    if await db.feds.find_one({'creator': user_id}):
        await message.reply(strings['can_only_1_fed'])
        return

    data = {
        'fed_name': fed_name,
        'fed_id': str(uuid.uuid4()),
        'creator': user_id
    }
    if await db.feds.insert_one(data):
        await message.reply(strings['created_fed'].format(
            name=fed_name, id=data['fed_id'], creator=await user_link_html(user_id)))


@decorator.register(cmds='joinfed')
@connection(admin=True, only_in_groups=True)
@get_strings_dec("feds")
async def join_fed_comm(message, strings, status, chat_id, chat_title, **kwargs):
    fed_id = message.get_args().split(' ')[0]
    peep = await tbot(
        GetParticipantRequest(
            channel=chat_id, user_id=message.from_user.id,
        )
    )
    if not peep.participant == ChannelParticipantCreator(user_id=message.from_user.id):
        await message.reply(get_string('feds', 'only_creators', chat_id))
        return

    # Assume Fed ID invalid
    if not (fed := await db.feds.find_one({'fed_id': fed_id})):
        await message.reply(get_string('feds', 'fed_id_invalid', chat_id))
        return

    # Assume chat already joined this/other fed
    if 'chats' in fed and chat_id in fed['chats']:
        await message.reply(get_string('feds', 'joined_fed_already', chat_id))
        return

    await db.feds.update_one(
        {'_id': fed['_id']},
        {"$addToSet": {'chats': {'$each': [chat_id]}}}
    )

    await message.reply(strings['join_fed_success'].format(name=fed['fed_name']))


@decorator.register(cmds='leavefed')
@connection(admin=True, only_in_groups=True)
@get_strings_dec("feds")
async def leave_fed_comm(message, strings, status, chat_id, chat_title, **kwargs):
    user = message.from_user.id
    peep = await tbot(
        GetParticipantRequest(
            channel=chat_id, user_id=user,
        )
    )
    if not peep.participant == ChannelParticipantCreator(user_id=user):
        await message.reply(get_string('feds', 'only_creators', chat_id))
        return

    if not (fed := await db.feds.find_one({'chats': {'$in': [chat_id]}})):
        await message.reply(get_string('feds', 'chat_not_in_fed', chat_id))
        return

    await db.feds.update_one(
        {'_id': fed['_id']},
        {'$pull': {'chats': chat_id}}
    )
    await message.reply(strings['leave_fed_success'])


@decorator.register(cmds='fpromote')
@connection(admin=True, only_in_groups=True)
@get_user_and_fed_and_text_dec
@user_is_fed_admin
@get_strings_dec("feds")
async def promote_to_fed(message, strings, user, fed, reason, status, chat_id, chat_title, **kwargs):
    fadmin_id = message.from_user.id
    user_id = user['user_id']

    if not fadmin_id == fed["creator"] and fadmin_id != OWNER_ID:
        await message.reply(strings["only_creator_promote"])
        return

    if await db.feds.find_one({'admins': {'$in': [user_id]}}):
        await message.reply(strings["admin_already_in_fed"].format(
            user=await user_link_html(user['user_id']), name=fed['fed_name']))
        return

    await db.feds.update_one(
        {'_id': fed['_id']},
        {"$addToSet": {'admins': {'$each': [user_id]}}}
    )
    await message.reply(strings["admin_added_to_fed"].format(
        user=await user_link_html(user['user_id']), name=fed['fed_name']))


@decorator.register(cmds='fdemote')
@connection(admin=True, only_in_groups=True)
@get_user_and_fed_and_text_dec
@user_is_fed_admin
@get_strings_dec("feds")
async def demote_from_fed(message, strings, user, fed, reason, status, chat_id, chat_title, **kwargs):
    fadmin_id = message.from_user.id
    user_id = user['user_id']

    if not fadmin_id == fed["creator"] and fadmin_id != OWNER_ID:
        await message.reply(strings["only_creator_promote"])
        return

    if 'admins' in fed and user_id not in fed['admins']:
        await message.reply(strings["admin_not_in_fed"].format(
            user=await user_link_html(user_id), name=fed['fed_name']))
        return

    await db.feds.update_one(
        {'_id': fed['_id']},
        {'$pull': {'admins': user_id}}
    )

    await message.reply(strings["admin_demoted_from_fed"].format(
        user=await user_link_html(user_id), name=fed['fed_name']))


@decorator.register(cmds='fchatlist')
@connection(admin=True, only_in_groups=True)
@get_fed_dec
@user_is_fed_admin
@get_strings_dec("feds")
async def fed_chat_list(message, strings, fed, status, chat_id, chat_title, **kwargs):
    text = strings['chats_in_fed'].format(name=fed['fed_name'])
    for chat_id in fed['chats']:
        chat = mongodb.chat_list.find_one({'chat_id': chat_id})
        text += '* {} (<code>{}</code>)\n'.format(chat["chat_title"], chat_id)
    if len(text) > 4096:
        await message.answer_document(
            types.InputFile(io.StringIO(text), filename="chatlist.txt"),
            "Output too large, sending as file",
            reply=message.message_id
        )
        return
    await message.reply(text)


@decorator.register(cmds='finfo')
@connection(admin=True, only_in_groups=True)
@get_fed_dec
@user_is_fed_admin
@get_strings_dec("feds")
async def fed_info(message, strings, fed, status, chat_id, chat_title, **kwargs):
    text = strings['fed_info']
    text += strings['fed_name'].format(name=fed['fed_name'])
    text += strings['fed_id'].format(id=fed['fed_id'])
    text += strings['fed_creator'].format(user=await user_link_html(fed['creator']))
    text += strings['chats_in_fed_info'].format(num=len(fed['chats'] if 'chats' in fed else []))
    text += strings['banned_in_fed_info'].format(num=len(fed['banned'] if 'banned' in fed else []))
    await message.reply(text)


@decorator.register(cmds=['fbanlist', 'fbanned'])
@connection(admin=True, only_in_groups=True)
@get_fed_dec
@user_is_fed_admin
@get_strings_dec("feds")
async def fbanned_list(message, strings, fed, status, chat_id, chat_title, **kwargs):
    if len(fed['banned']) < 1:
        await message.reply(strings['no_fbanned_in_fed'].format(fed_name=fed['fed_name']))
        return

    if message.get_args().split(' ')[0].lower() == 'json':
        file_name = "fbanned_users_list.json"
        fed['banned']['json_info'] = {
            'sophie_ver': SOPHIE_VERSION,
            'fed_id': fed['fed_id'],
            'version': 1,
            'time': datetime.datetime.now()
        }
        data = ujson.dumps(fed['banned'], indent=2)

    elif message.get_args().split(' ')[0].lower() == 'csv':
        file_name = "fbanned_users_list.csv"
        data = 'id,reason'
        for user_id in fed['banned']:
            banned_user = fed['banned'][user_id]
            data += '\n' + user_id
            if data and 'reason' in banned_user and banned_user['reason']:
                data += ',' + banned_user['reason']

    else:
        file_name = "fbanned_users_list.txt"
        data = strings['fbanned_list_header'].format(fed_name=fed['fed_name'], fed_id=fed['fed_id'])
        for user_id in fed['banned']:
            banned_user = fed['banned'][user_id]
            if user := await db.user_list.find_one({'user_id': user_id}):
                print(user)
                data += f"\n {user['first_name']} "
                if 'last_name' in user and user['last_name']:
                    data += user['last_name']
                data += f" ({user_id})"
            else:
                data += f'\n ({user_id})'

            # Reason
            if data and 'reason' in banned_user and banned_user['reason']:
                data += ': ' + banned_user['reason']
            else:
                data += ': No reason'
    await message.answer_document(
        types.InputFile(io.StringIO(data), filename=file_name),
        strings['fbanned_list_msg'].format(fed_name=fed['fed_name'], fed_id=fed['fed_id']),
        reply=message.message_id
    )


@decorator.register(cmds='fban')
@connection(admin=True, only_in_groups=True)
@get_user_and_fed_and_text_dec
@user_is_fed_admin
@get_strings_dec("feds")
async def fban_user(message, strings, user, fed, reason, status, chat_id, chat_title, **kwargs):
    if not reason:
        reason = None
    user_id = user['user_id']

    if user_id in WHITELISTED:
        await message.reply(strings['user_wl'])
        return

    elif user_id == BOT_ID:
        await message.reply(strings['fban_self'])
        return

    elif user_id == fed['creator']:
        await message.reply(strings['fban_creator'])
        return

    elif 'admins' in fed and user_id in fed['admins']:
        await message.reply(strings['fban_fed_admin'])
        return

    elif 'banned' in fed and str(user_id) in fed['banned']:
        await message.reply(strings['already_fbanned'].format(user=await user_link_html(user['user_id'])))
        return

    fed_name = fed['fed_name']

    text = strings['fbanned_header']
    text += strings['fbanned_fed'].format(fed=fed_name)
    text += strings['fbanned_fadmin'].format(fadmin=await user_link_html(message.from_user.id))
    text += strings['fbanned_user'].format(
        user=await user_link_html(user['user_id']) + f" (<code>{user['user_id']}</code>)")
    if reason:
        text += strings['fbanned_reason'].format(reason=reason)

    msg = await message.reply(text + strings['fbanned_process'].format(num=len(fed['chats'])))

    banned_chats = []
    for chat_id in fed['chats']:
        await asyncio.sleep(0.3)  # Do not slow down other updates
        try:
            await bot.kick_chat_member(chat_id, user['user_id'])
            banned_chats.append(chat_id)

        except Exception:
            continue

    await msg.edit_text(text + strings['fbanned_done'].format(num=len(banned_chats)))

    new = {
        'user_id': user['user_id'],
        'banned_chats': banned_chats,
        'time': datetime.datetime.now(),
        'reason': reason
    }

    await db.feds.update_one(
        {'_id': fed['_id']},
        {"$set": {f'banned.{user_id}': new}}
    )

    # TODO(Notify all fedadmins)


@decorator.register(cmds='unfban')
@connection(admin=True, only_in_groups=True)
@get_user_and_fed_and_text_dec
@user_is_fed_admin
@get_strings_dec("feds")
async def un_fban_user(message, strings, user, fed, reason, status, chat_id, chat_title, **kwargs):
    from_id = message.from_user.id
    user_id = user['user_id']
    if user == BOT_ID:
        await message.reply(strings['unfban_self'])
        return

    elif str(user_id) not in fed['banned']:
        await message.reply(strings['user_not_fbanned'].format(user=await user_link_html(user['user_id'])))
        return

    text = strings['un_fbanned_header']
    text += strings['fbanned_fed'].format(fed=fed["fed_name"])
    text += strings['fbanned_fadmin'].format(fadmin=await user_link_html(from_id))
    text += strings['fbanned_user'].format(
        user=await user_link_html(user['user_id']) + f" (<code>{user['user_id']}</code>)")

    banned_chats = fed['banned'][str(user_id)]['banned_chats']

    msg = await message.reply(text + strings['un_fbanned_process'].format(num=len(banned_chats)))

    counter = 0
    for chat_id in banned_chats:
        await asyncio.sleep(0.3)  # Do not slow down other updates
        try:
            await bot.unban_chat_member(
                chat_id,
                user_id
            )
            counter += 1

        except Exception:
            continue

    await db.feds.update_one(
        {'_id': fed['_id']},
        {"$unset": {f'banned.{user_id}': 1}}
    )

    await msg.edit_text(text + strings['un_fbanned_done'].format(num=counter))


# Functions


@decorator.register(only_groups=True)
@get_strings_dec('feds')
async def fban_helper(message, strings):
    chat_id = message.chat.id
    user_id = message.from_user.id

    fed = await db.feds.find_one({'chat_id': chat_id})
    if not fed:
        return

    if str(user_id) not in fed['banned']:
        return

    if await is_user_admin(chat_id, user_id) is True:
        return

    try:
        await bot.kick_chat_member(chat_id, user_id)
    except Exception:
        return  # TODO: warn chat admins

    await db.feds.update_one(
        {'_id': fed['_id']},
        {"$addToSet": {f'banned.{user_id}.banned_chats': {'$each': [chat_id]}}}
    )

    await message.reply(strings['fban_usr_rmvd'].format(
        fed=fed['fed_name'],
        user=await user_link_html(user_id),
        rsn=fed['banned'][str(user_id)]['reason']
    ))
