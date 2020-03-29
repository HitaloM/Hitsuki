# Copyright (C) 2018 - 2020 MrYacha. All rights reserved. Source code available under the AGPL.
# Copyright (C) 2019 Aiogram

#
# This file is part of SophieBot.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import datetime
import io
import uuid

from aiogram.types import InputFile

from sophie_bot import OWNER_ID, BOT_ID, OPERATORS, decorator, bot
from sophie_bot.services.mongo import db
from .utils.connections import get_connected_chat, chat_connection
from .utils.language import get_strings_dec, get_string
from .utils.message import need_args_dec
from .utils.restrictions import ban_user, unban_user
from .utils.user_details import is_chat_creator, get_user_link, get_user_and_text


# functions

async def get_fed_f(message, chat_id):
    chat = await get_connected_chat(message, admin=True, only_groups=True)
    fed = await db.feds.find_one({'chats': {'$in': [chat['chat_id']]}})
    if not fed:
        return False
    return fed


async def fed_post_log(fed, text):
    if 'log_chat_id' not in fed:
        return
    chat_id = fed['log_chat_id']
    await bot.send_message(chat_id, text)


# decorators

def get_current_chat_fed(func):
    async def wrapped_1(*args, **kwargs):
        message = args[0]
        real_chat_id = message.chat.id
        if not (fed := await get_fed_f(message, message.chat.id)):
            await message.reply(get_string(real_chat_id, "feds", 'chat_not_in_fed'))
            return

        return await func(*args, fed, **kwargs)

    return wrapped_1


def get_fed_user_text(func):
    async def wrapped_1(*args, **kwargs):
        fed = None
        message = args[0]
        real_chat_id = message.chat.id
        user, text = await get_user_and_text(message, send_text=False)

        # Check nonexits user
        if not user and (args := message.get_args().split(None, 1))[0].isdigit():
            user = {'user_id': args[0]}
            text = args[1] if len(args) > 1 else None
        elif not user:
            await message.reply("I can't get this user.")

        # Check fed_id in args
        if text:
            text_args = text.split(" ", 1)
            if len(text_args) >= 1:
                if text_args[0].count('-') == 4:
                    text = text_args[1] if len(text_args) > 1 else ''
                    if not (fed := await db.feds.find_one({'fed_id': text_args[0]})):
                        await message.reply(get_string(real_chat_id, "feds", 'fed_id_invalid'))
                        return
                else:
                    text = " ".join(text_args)

        if not fed:
            if not (fed := await get_fed_f(message, message.chat.id)):
                await message.reply(get_string(real_chat_id, "feds", 'chat_not_in_fed'))
                return

        return await func(*args, fed, user, text, **kwargs)

    return wrapped_1


def get_fed_dec(func):
    async def wrapped_1(*args, **kwargs):
        fed = None
        message = args[0]
        real_chat_id = message.chat.id

        if message.text:
            text_args = message.text.split(" ", 1)
            if not len(text_args) < 2 and text_args[1].count('-') == 4:
                if not (fed := await db.feds.find_one({'fed_id': text_args[1]})):
                    await message.reply(get_string(real_chat_id, "feds", 'fed_id_invalid'))
                    return

        if not (fed := await get_fed_f(message, message.chat.id)):
            await message.reply(await get_string(real_chat_id, "feds", 'chat_not_in_fed'))
            return

        return await func(*args, fed, **kwargs)

    return wrapped_1


def is_fed_owner(func):
    async def wrapped_1(*args, **kwargs):
        message = args[0]
        fed = args[1]
        user_id = message.from_user.id

        if not user_id == fed["creator"] and user_id != OWNER_ID:
            await message.reply(get_string(message.chat.id, "feds", 'need_fed_admin').format(name=fed['fed_name']))
            return

        return await func(*args, **kwargs)

    return wrapped_1


def is_fed_admin(func):
    async def wrapped_1(*args, **kwargs):
        message = args[0]
        fed = args[1]
        user_id = message.from_user.id

        if not user_id == fed["creator"] and user_id != OWNER_ID:
            if user_id not in fed['admins']:
                await message.reply(get_string(message.chat.id, "feds", 'need_fed_admin').format(name=fed['fed_name']))

        return await func(*args, **kwargs)

    return wrapped_1


# cmds


@decorator.register(cmds=['newfed', 'fnew'])
@get_strings_dec("feds")
async def new_fed(message, strings):
    fed_name = message.get_args()
    user_id = message.from_user.id
    if not fed_name:
        await message.reply(strings['no_args'])

    if len(fed_name) > 60:
        await message.reply(strings['fed_name_long'])
        return

    if await db.feds.find_one({'creator': user_id}) and not user_id == OWNER_ID:
        await message.reply(strings['can_only_1_fed'])
        return

    if await db.feds.find_one({'fed_name': fed_name}):
        await message.reply(strings['name_not_avaible'])
        return

    data = {
        'fed_name': fed_name,
        'fed_id': str(uuid.uuid4()),
        'creator': user_id
    }
    await db.feds.insert_one(data)
    await message.reply(strings['created_fed'].format(
        name=fed_name, id=data['fed_id'], creator=await get_user_link(user_id)
    ))


@decorator.register(cmds=['joinfed', 'fjoin'])
@need_args_dec()
@chat_connection(admin=True, only_groups=True)
@get_strings_dec("feds")
async def join_fed(message, chat, strings):
    fed_id = message.get_args().split(' ')[0]
    user_id = message.from_user.id
    chat_id = chat['chat_id']

    if not await is_chat_creator(chat_id, user_id):
        await message.reply(strings['only_creators'])

    # Assume Fed ID invalid
    if not (fed := await db.feds.find_one({'fed_id': fed_id})):
        await message.reply(strings['fed_id_invalid'])
        return

    # Assume chat already joined this/other fed
    if 'chats' in fed and chat_id in fed['chats']:
        await message.reply(strings['joined_fed_already'])
        return

    await db.feds.update_one(
        {'_id': fed['_id']},
        {"$addToSet": {'chats': {'$each': [chat_id]}}}
    )

    await message.reply(strings['join_fed_success'].format(chat=chat['chat_title'], fed=fed['fed_name']))
    await fed_post_log(fed, strings['join_chat_fed_log'].format(
        fed_name=fed['fed_name'],
        fed_id=fed['fed_id'],
        chat_name=chat['chat_title'],
        chat_id=chat_id
    ))


@decorator.register(cmds=['leavefed', 'fleave'])
@chat_connection(admin=True, only_groups=True)
@get_current_chat_fed
@get_strings_dec("feds")
async def leave_fed_comm(message, chat, fed, strings):
    user_id = message.from_user.id
    if not await is_chat_creator(chat['chat_id'], user_id):
        await message.reply(strings['only_creators'])

    await db.feds.update_one(
        {'_id': fed['_id']},
        {'$pull': {'chats': chat['chat_id']}}
    )
    await message.reply(strings['leave_fed_success'].format(chat=chat['chat_title'], fed=fed['fed_name']))

    await fed_post_log(fed, strings['leave_chat_fed_log'].format(
        fed_name=fed['fed_name'],
        fed_id=fed['fed_id'],
        chat_name=chat['chat_title'],
        chat_id=chat['chat_id']
    ))


@decorator.register(cmds='fsub')
@need_args_dec()
@get_current_chat_fed
@is_fed_owner
@get_strings_dec("feds")
async def fed_sub(message, fed, strings):
    fed_id = message.get_args().split(' ')[0]

    # Assume Fed ID is valid
    if not (fed2 := await db.feds.find_one({'fed_id': fed_id})):
        await message.reply(strings['fed_id_invalid'])
        return

    # Assume chat already joined this/other fed
    if 'subscribed' in fed and fed_id in fed['subscribed']:
        message.reply(strings['already_subsed'].format(
            name=fed['fed_name'],
            name2=fed2['fed_name']
        ))
        return

    await db.feds.update_one(
        {'_id': fed['_id']},
        {"$addToSet": {'subscribed': {'$each': [fed_id]}}}
    )

    await message.reply(strings['subsed_success'].format(
        name=fed['fed_name'],
        name2=fed2['fed_name']
    ))


@decorator.register(cmds='fpromote')
@get_fed_user_text
@is_fed_owner
@get_strings_dec("feds")
async def promote_to_fed(message, fed, user, text, strings):
    await db.feds.update_one(
        {'_id': fed['_id']},
        {"$addToSet": {'admins': {'$each': [user['user_id']]}}}
    )
    await message.reply(strings["admin_added_to_fed"].format(
        user=await get_user_link(user['user_id']), name=fed['fed_name'])
    )

    await fed_post_log(fed, strings['promote_user_fed_log'].format(
        fed_name=fed['fed_name'],
        fed_id=fed['fed_id'],
        user=await get_user_link(user['user_id']),
        user_id=user['user_id']
    ))


@decorator.register(cmds='fdemote')
@get_fed_user_text
@is_fed_owner
@get_strings_dec("feds")
async def demote_from_fed(message, fed, user, text, strings):
    await db.feds.update_one(
        {'_id': fed['_id']},
        {'$pull': {'admins': user['user_id']}}
    )

    await message.reply(strings["admin_demoted_from_fed"].format(
        user=await get_user_link(user['user_id']), name=fed['fed_name'])
    )

    await fed_post_log(fed, strings['demote_user_fed_log'].format(
        fed_name=fed['fed_name'],
        fed_id=fed['fed_id'],
        user=await get_user_link(user['user_id']),
        user_id=user['user_id']
    ))


@decorator.register(cmds=['fsetlog', 'setfedlog'], only_groups=True)
@get_fed_dec
@is_fed_owner
@get_strings_dec("feds")
async def set_fed_log_chat(message, fed, strings):
    if 'log_chat_id' in fed and fed['log_chat_id']:
        await message.reply(strings['already_have_chatlog'].format(name=fed['fed_name']))
        return

    await db.feds.update_one(
        {'_id': fed['_id']},
        {'$set': {'log_chat_id': message.chat.id}}
    )

    text = strings['set_chat_log'].format(name=fed['fed_name'])
    await message.reply(text)

    await fed_post_log(fed.update({'log_chat_id': message.chat.id}), strings['set_log_fed_log'].format(
        fed_name=fed['fed_name'],
        fed_id=fed['fed_id']
    ))


@decorator.register(cmds=['funsetlog', 'unsetfedlog'], only_groups=True)
@get_fed_dec
@is_fed_owner
@get_strings_dec("feds")
async def unset_fed_log_chat(message, fed, strings):
    if 'log_chat_id' not in fed or not fed['log_chat_id']:
        await message.reply(strings['already_have_chatlog'].format(name=fed['fed_name']))
        return

    await db.feds.update_one(
        {'_id': fed['_id']},
        {'$unset': {'log_chat_id': 1}}
    )

    text = strings['logging_removed'].format(name=fed['fed_name'])
    await message.reply(text)

    await fed_post_log(fed, strings['unset_log_fed_log'].format(
        fed_name=fed['fed_name'],
        fed_id=fed['fed_id']
    ))


@decorator.register(cmds=['fchatlist', 'fchats'])
@get_fed_dec
@is_fed_admin
@get_strings_dec("feds")
async def fed_chat_list(message, fed, strings):
    text = strings['chats_in_fed'].format(name=fed['fed_name'])
    for chat_id in fed['chats']:
        chat = await db.chat_list.find_one({'chat_id': chat_id})
        text += '* {} (<code>{}</code>)\n'.format(chat["chat_title"], chat_id)
    if len(text) > 4096:
        await message.answer_document(
            InputFile(io.StringIO(text), filename="chatlist.txt"),
            strings['too_large'],
            reply=message.message_id
        )
        return
    await message.reply(text)


@decorator.register(cmds=['fadminlist', 'fadmins'])
@get_fed_dec
@is_fed_admin
@get_strings_dec("feds")
async def fed_admins_list(message, fed, strings):
    text = strings['fadmins_header'].format(fed_name=fed['fed_name'])
    text += '* {} (<code>{}</code>)\n'.format(await get_user_link(fed['creator']), fed['creator'])
    for user_id in fed['admins']:
        text += '* {} (<code>{}</code>)\n'.format(await get_user_link(user_id), user_id)
    await message.reply(text)


@decorator.register(cmds='finfo')
@get_fed_dec
@get_strings_dec("feds")
async def fed_info(message, fed, strings):
    text = strings['finfo_text']
    text = text.format(
        name=fed['fed_name'],
        fed_id=fed['fed_id'],
        creator=await get_user_link(fed['creator']),
        chats=len(fed['chats'] if 'chats' in fed else []),
        fbanned=len(fed['banned'] if 'banned' in fed else [])
    )

    if 'subscribed' in fed and len(fed['subscribed']) > 0:
        text += strings['finfo_subs_title']
        for sfed in fed['subscribed']:
            sfed = await db.feds.find_one({'fed_id': sfed})
            text += f"* {sfed['fed_name']} (<code>{sfed['fed_id']}</code>)\n"

    await message.reply(text)


async def get_all_subs_feds_r(fed_id, new):
    new.append(fed_id)

    fed = await db.feds.find_one({'fed_id': fed_id})
    async for item in db.feds.find({'subscribed': {'$in': [fed['fed_id']]}}):
        new = await get_all_subs_feds_r(item['fed_id'], new)

    return new


@decorator.register(cmds='fban')
@get_fed_user_text
@is_fed_admin
@get_strings_dec("feds")
async def fed_ban_user(message, fed, user, reason, strings):
    user_id = user['user_id']

    # Checks
    if user_id in OPERATORS:
        await message.reply(strings['user_wl'])
        return

    elif user_id == message.from_user.id:
        await message.reply(strings['fban_self'])
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
        await message.reply(strings['already_fbanned'].format(user=await get_user_link(user['user_id'])))
        return

    text = strings['fbanned_header']
    text += strings['fban_info'].format(
        fed=fed['fed_name'],
        fadmin=await get_user_link(message.from_user.id),
        user=await get_user_link(user['user_id']),
        user_id=user['user_id']
    )
    if reason:
        text += strings['fbanned_reason'].format(reason=reason)

    # fban processing msg
    msg = await message.reply(text + strings['fbanned_process'].format(num=len(fed['chats'])))

    user = await db.user_list.find_one({'user_id': user_id})

    banned_chats = []
    for chat_id in fed['chats']:
        if chat_id in user['chats']:
            await asyncio.sleep(0.2)  # Do not slow down other updates
            if await ban_user(chat_id, user_id):
                banned_chats.append(chat_id)

    new = {
        'banned_chats': banned_chats,
        'time': datetime.datetime.now(),
        'by': message.from_user.id
    }

    if text:
        new['reason'] = text

    await db.feds.update_one(
        {'_id': fed['_id']},
        {"$set": {f'banned.{user_id}': new}}
    )

    channel_text = strings['fban_log_fed_log'].format(
        fed_name=fed['fed_name'],
        fed_id=fed['fed_id'],
        user=await get_user_link(user['user_id']),
        user_id=user['user_id'],
        chat_count=len(banned_chats),
        all_chats=len(fed['chats'])
    )

    if reason:
        channel_text += strings['fban_reason_fed_log'].format(reason=reason)

    # SubsFeds process
    if len(sfeds_list := await get_all_subs_feds_r(fed['fed_id'], [])) > 1:
        sfeds_list.remove(fed['fed_id'])
        this_fed_banned_count = len(banned_chats)

        await msg.edit_text(text + strings['fbanned_subs_process'].format(feds=len(sfeds_list)))

        all_banned_chats_count = 0
        for sfed in sfeds_list:
            sfed = await db.feds.find_one({'fed_id': sfed})
            banned_chats = []
            for chat_id in sfed['chats']:
                if chat_id not in user['chats']:
                    continue

                await asyncio.sleep(0.2)  # Do not slow down other updates

                if await ban_user(chat_id, user_id):
                    banned_chats.append(chat_id)
                    all_banned_chats_count += 1

                    new = {
                        'banned_chats': banned_chats,
                        'time': datetime.datetime.now(),
                        'origin_fed': fed['fed_id'],
                        'by': message.from_user.id
                    }

                    await db.feds.update_one({'_id': sfed['_id']}, {'$set': {f'banned.{user_id}': new}})

        await msg.edit_text(text + strings['fbanned_subs_done'].format(
            chats=this_fed_banned_count,
            subs_chats=all_banned_chats_count,
            feds=len(sfeds_list)
        ))

        channel_text += strings['fban_subs_fed_log'].format(
            subs_chats=all_banned_chats_count,
            feds=len(sfeds_list)
        )

    else:
        await msg.edit_text(text + strings['fbanned_done'].format(num=len(banned_chats)))

    await fed_post_log(fed, channel_text)


@decorator.register(cmds=['unfban', 'funban'])
@get_fed_user_text
@is_fed_admin
@get_strings_dec("feds")
async def unfed_ban_user(message, fed, user, text, strings):
    user_id = user['user_id']

    if user == BOT_ID:
        await message.reply(strings['unfban_self'])
        return

    elif str(user_id) not in fed['banned']:
        await message.reply(strings['user_not_fbanned'].format(user=await get_user_link(user['user_id'])))
        return

    text = strings['un_fbanned_header']
    text += strings['fban_info'].format(
        fed=fed['fed_name'],
        fadmin=await get_user_link(message.from_user.id),
        user=await get_user_link(user['user_id']),
        user_id=user['user_id']
    )

    banned_chats = fed['banned'][str(user_id)]['banned_chats']

    # unfban processing msg
    msg = await message.reply(text + strings['un_fbanned_process'].format(num=len(banned_chats)))

    counter = 0
    for chat_id in banned_chats:
        await asyncio.sleep(0.2)  # Do not slow down other updates
        if await unban_user(chat_id, user_id):
            counter += 1

    await db.feds.update_one(
        {'_id': fed['_id']},
        {"$unset": {f'banned.{user_id}': 1}}
    )

    channel_text = strings['un_fban_log_fed_log'].format(
        fed_name=fed['fed_name'],
        fed_id=fed['fed_id'],
        user=await get_user_link(user['user_id']),
        user_id=user['user_id'],
        chat_count=len(banned_chats),
        all_chats=len(fed['chats'])
    )

    # Subs feds
    if len(sfeds_list := await get_all_subs_feds_r(fed['fed_id'], [])) > 1:
        sfeds_list.remove(fed['fed_id'])
        this_fed_unbanned_count = counter

        await msg.edit_text(text + strings['un_fbanned_subs_process'].format(feds=len(sfeds_list)))

        all_unbanned_chats_count = 0
        for sfed in sfeds_list:
            sfed = await db.feds.find_one({'fed_id': sfed})

            banned_chats = fed['banned'][str(user_id)]['banned_chats']
            for chat_id in banned_chats:
                await asyncio.sleep(0.2)  # Do not slow down other updates
                if await unban_user(chat_id, user_id):
                    banned_chats.append(chat_id)
                    all_unbanned_chats_count += 1

                    await db.feds.update_one(
                        {'_id': sfed['_id']},
                        {"$unset": {f'banned.{user_id}': 1}}
                    )

        await msg.edit_text(text + strings['un_fbanned_subs_done'].format(
            chats=this_fed_unbanned_count,
            subs_chats=all_unbanned_chats_count,
            feds=len(sfeds_list)
        ))

        channel_text += strings['fban_subs_fed_log'].format(
            subs_chats=all_unbanned_chats_count,
            feds=len(sfeds_list)
        )
    else:
        await msg.edit_text(text + strings['un_fbanned_done'].format(num=counter))

    await fed_post_log(fed, channel_text)
