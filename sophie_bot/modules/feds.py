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
import uuid
import io

from telethon.tl.functions.channels import (EditBannedRequest,
                                            GetParticipantRequest)
from telethon.tl.types import ChannelParticipantCreator, ChatBannedRights

from aiogram import types

from sophie_bot import OWNER_ID, BOT_ID, WHITELISTED, tbot, decorator, mongodb, bot
from sophie_bot.modules.language import get_string, get_strings_dec
from sophie_bot.modules.users import (is_user_admin, user_link,
                                      get_user_and_text, user_link_html)
from sophie_bot.modules.connections import connection, get_conn_chat


def get_user_and_fed_and_text_dec(func):
    async def wrapped_1(message, status, chat_id, chat_title, *args, **kwargs):
        user, text = await get_user_and_text(message)
        if not user:
            return

        chat_fed = None

        if text:
            args = text.split(" ", 1)

            if len(args) >= 1:
                # Check if args[0] is a FedID
                F = 0
                for symbol in args[0]:
                    if symbol == "-":
                        F += 1

                if F == 4:
                    text = args[1]
                    chat_fed = mongodb.fed_list.find_one({'fed_id': args[0]})
                    if not chat_fed:
                        await message.reply(get_string("feds", 'fed_id_invalid', message.chat.id))
                        return
                else:
                    text = "".join(args)

        if not chat_fed:
            chat_fed = mongodb.fed_groups.find_one({'chat_id': chat_id})
            if not chat_fed:
                await message.reply(get_string("feds", 'chat_not_in_fed', message.chat.id))
                return

        fed = mongodb.fed_list.find_one({'fed_id': chat_fed['fed_id']})

        return await func(message, status, chat_id, chat_title, user, fed, text, *args, **kwargs)
    return wrapped_1


def get_fed_dec(func):
    async def wrapped_1(message, status, chat_id, chat_title, *args, **kwargs):
        chat_fed = None

        arg = message.text.split(' ', 2)
        if not len(arg) < 2:
            arg = arg[1]

            # Check if arg is a FedID
            F = 0
            for symbol in arg:
                if symbol == "-":
                    F += 1

            if F == 4:
                chat_fed = mongodb.fed_list.find_one({'fed_id': arg})
                if not chat_fed:
                    await message.reply(get_string("feds", 'fed_id_invalid', message.chat.id))
                    return

        if not chat_fed:
            chat_fed = mongodb.fed_groups.find_one({'chat_id': chat_id})
            if not chat_fed:
                await message.reply(get_string("feds", 'chat_not_in_fed', message.chat.id))
                return

        fed = mongodb.fed_list.find_one({'fed_id': chat_fed['fed_id']})

        return await func(message, status, chat_id, chat_title, fed, *args, **kwargs)
    return wrapped_1


def user_is_fed_admin(func):
    async def wrapped_1(event, *args, **kwargs):

        if hasattr(event, 'from_id'):
            user_id = event.from_id
        elif 'from' in event:
            user_id = event.from_user.id

        if user_id == OWNER_ID:
            return await func(event, *args, **kwargs)

        if hasattr(event, 'chat_id'):
            real_chat_id = event.chat_id
        elif hasattr(event, 'chat'):
            real_chat_id = event.chat.id

        status, chat_id, chat_title = await get_conn_chat(
            user_id, real_chat_id, only_in_groups=True)

        group_fed = mongodb.fed_groups.find_one({'chat_id': chat_id})
        if not group_fed:
            await event.reply(get_string("feds", 'chat_not_in_fed', real_chat_id))
            return False
        fed = mongodb.fed_list.find_one({'fed_id': group_fed['fed_id']})
        if not user_id == fed['creator']:
            fadmins = mongodb.fed_admins.find({'fed_id': fed['fed_id'], 'admin': user_id})
            if not fadmins:
                await event.reply(get_string("feds", 'need_admin_to_fban', real_chat_id).format(
                    name=fed['fed_name']))
        return await func(event, *args, **kwargs)
    return wrapped_1


# Commands


@decorator.register(cmds='newfed')
@get_strings_dec("feds")
async def newFed(message, strings, **kwargs):
    args = message.get_args()
    if not args:
        await message.reply(strings['no_args'])
    fed_name = args
    creator = message.from_user.id
    fed_id = str(uuid.uuid4())
    data = {'fed_name': fed_name, 'fed_id': fed_id, 'creator': creator}
    check = mongodb.fed_list.insert_one(data)
    if check:
        await message.reply(strings['created_fed'].format(
            name=fed_name, id=fed_id, creator=await user_link_html(creator)))


@decorator.register(cmds='joinfed')
@get_strings_dec("feds")
async def join_fed_comm(message, strings, **kwargs):
    fed_id = message.get_args()
    chat_id = message.chat.id
    user = message.from_user.id
    peep = await tbot(
        GetParticipantRequest(
            channel=chat_id, user_id=user,
        )
    )
    if not peep.participant == ChannelParticipantCreator(user_id=user):
        await message.reply(get_string('feds', 'only_creators', chat_id))
        return

    check = mongodb.fed_list.find_one({'fed_id': fed_id})
    if check is False:  # Assume Fed ID invalid
        await message.reply(get_string('feds', 'fed_id_invalid', chat_id))
        return

    old = mongodb.fed_groups.find_one({'chat_id': chat_id})
    if old:  # Assume chat already joined this/other fed
        await message.reply(get_string('feds', 'joined_fed_already', chat_id))
        return

    join_data = {'chat_id': chat_id, 'fed_id': fed_id}
    mongodb.fed_groups.insert_one(join_data)

    await message.reply(strings['join_fed_success'].format(name=check['fed_name']))


@decorator.register(cmds='leavefed')
@get_strings_dec("feds")
async def leave_fed_comm(message, strings, **kwargs):
    chat_id = message.chat.id
    user = message.from_user.id
    peep = await tbot(
        GetParticipantRequest(
            channel=chat_id, user_id=user,
        )
    )
    if not peep.participant == ChannelParticipantCreator(user_id=user):
        await message.reply(get_string('feds', 'only_creators', chat_id))
        return

    old = mongodb.fed_groups.delete_one({'chat_id': chat_id}).deleted_count
    if old < 1:  # If chat not was in any federation
        await message.reply(get_string('feds', 'chat_not_in_fed', chat_id))
        return
    await message.reply(strings['leave_fed_success'])


@decorator.register(cmds='fpromote')
@connection(admin=True, only_in_groups=True)
@get_user_and_fed_and_text_dec
@user_is_fed_admin
@get_strings_dec("feds")
async def promote_to_fed(message, strings, status, chat_id, chat_title, user, fed, reason,
                         *args, **kwargs):
    user_id = message.from_user.id

    if not user_id == fed["creator"] and user_id != OWNER_ID:
        await message.reply(strings["only_creator_promote"])
        return
    data = {'fed_id': fed['fed_id'], 'admin': user['user_id']}

    old = mongodb.fed_admins.find_one(data)
    if old:
        await message.reply(strings["admin_already_in_fed"].format(
            user=await user_link_html(user['user_id']), name=fed['fed_name']))
        return
    mongodb.fed_admins.insert_one(data)
    await message.reply(strings["admin_added_to_fed"].format(
        user=await user_link_html(user['user_id']), name=fed['fed_name']))


@decorator.register(cmds='fdemote')
@connection(admin=True, only_in_groups=True)
@get_user_and_fed_and_text_dec
@user_is_fed_admin
@get_strings_dec("feds")
async def demote_from_fed(message, strings, status, chat_id, chat_title, user, fed, reason,
                          *args, **kwargs):
    user_id = message.from_user.id

    if not user_id == fed["creator"] and user_id != OWNER_ID:
        await message.reply(strings["only_creator_promote"])
        return
    data = {'fed_id': fed['fed_id'], 'admin': user['user_id']}

    old = mongodb.fed_admins.find_one(data)
    if not old:
        await message.reply(strings["admin_not_in_fed"].format(
            user=await user_link_html(user['user_id']), name=fed['fed_name']))
        return
    mongodb.fed_admins.delete_one({'_id': old['_id']})
    await message.reply(strings["admin_demoted_from_fed"].format(
        user=await user_link_html(user['user_id']), name=fed['fed_name']))


@decorator.register(cmds='fchatlist')
@connection(admin=True, only_in_groups=True)
@get_fed_dec
@user_is_fed_admin
@get_strings_dec("feds")
async def fed_chat_list(message, strings, status, chat_id, chat_title, fed,
                        *args, **kwargs):
    text = strings['chats_in_fed'].format(name=fed['fed_name'])
    chats = mongodb.fed_groups.find({'fed_id': fed['fed_id']})
    for fed in chats:
        chat = mongodb.chat_list.find_one({'chat_id': fed['chat_id']})
        text += '* {} (<code>{}</code>)\n'.format(chat["chat_title"], fed['chat_id'])
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
async def fed_info(message, strings, status, chat_id, chat_title, fed,
                   *args, **kwargs):
    text = strings['fed_info']
    text += strings['fed_name'].format(name=fed['fed_name'])
    text += strings['fed_id'].format(id=fed['fed_id'])
    text += strings['fed_creator'].format(user=await user_link_html(fed['creator']))
    chats = mongodb.fed_groups.find({'fed_id': fed['fed_id']})
    text += strings['chats_in_fed_info'].format(num=chats.count())
    fbans = mongodb.fbanned_users.find({'fed_id': fed['fed_id']})
    text += strings['banned_in_fed_info'].format(num=fbans.count())
    await message.reply(text)


@decorator.register(cmds='fbanned')
@connection(admin=True, only_in_groups=True)
@get_fed_dec
@user_is_fed_admin
@get_strings_dec("feds")
async def fbanned_list(message, strings, status, chat_id, chat_title, fed,
                       *args, **kwargs):
    fbanned = mongodb.fbanned_users.find({'fed_id': fed['fed_id']})
    if not fbanned or fbanned.count() == 0:
        await message.reply(strings['no_fbanned_in_fed'].format(fed_name=fed['fed_name']))
        return
    text = strings['fbanned_list_header'].format(fed_name=fed['fed_name'], fed_id=fed['fed_id'])
    for user_id in fbanned:
        user_id = user_id['user']
        user = mongodb.user_list.find_one({'user_id': user_id})
        fbanned = mongodb.fbanned_users.find_one({'fed_id': fed['fed_id'], 'user_id': user_id})
        if user:
            text += f"\n {user['first_name']} "
            if 'last_name' in user and user['last_name']:
                text += user['last_name']
            text += f" ({user_id})"
        else:
            text += f'\n ({user_id})'
        if fbanned and 'reason' in fbanned:
            text += ': ' + fbanned['reason']
    await message.answer_document(
        types.InputFile(io.StringIO(text), filename="fbanned_list.txt"),
        strings['fbanned_list_header'].format(fed_name=fed['fed_name'], fed_id=fed['fed_id']),
        reply=message.message_id
    )


@decorator.register(cmds='fban')
@connection(admin=True, only_in_groups=True)
@get_user_and_fed_and_text_dec
@user_is_fed_admin
@get_strings_dec("feds")
async def fban_user(message, strings, status, chat_id, chat_title, user, fed, reason,
                    *args, **kwargs):

    if not reason:
        reason = 'No reason'

    if user['user_id'] in WHITELISTED:
        await message.reply(strings['user_wl'])
        return

    elif user['user_id'] == BOT_ID:
        await message.reply(strings['fban_self'])
        return

    elif user['user_id'] == fed['creator']:
        await message.reply(strings['fban_creator'])
        return

    if mongodb.fed_admins.find_one(
            {'fed_id': fed['fed_id'], 'admin': user['user_id']}):
        await message.reply(strings['fban_fed_admin'])
        return

    check = mongodb.fbanned_users.find_one({'user': user['user_id'], 'fed_id': fed['fed_id']})
    if check:
        await message.reply(strings['already_fbanned'].format(
                            user=await user_link_html(user['user_id'])))
        return

    fed_name = mongodb.fed_list.find_one({'fed_id': fed['fed_id']})['fed_name']

    text = strings['fbanned_header']
    text += strings['fbanned_fed'].format(fed=fed_name)
    text += strings['fbanned_fadmin'].format(fadmin=await user_link_html(message.from_user.id))
    text += strings['fbanned_user'].format(
        user=await user_link_html(user['user_id']) + f" (<code>{user['user_id']}</code>)")
    text += strings['fbanned_reason'].format(reason=reason)

    fed_chats = mongodb.fed_groups.find({'fed_id': fed['fed_id']})

    msg = await message.reply(text + strings['fbanned_process'].format(num=fed_chats.count()))

    counter = 0
    for chat in fed_chats:
        await asyncio.sleep(0.5)  # Do not slow down other updates
        try:
            await bot.kick_chat_member(message.chat.id, user['user_id'])
            counter += 1

        except Exception:
            continue

    await msg.edit_text(text + strings['fbanned_done'].format(num=counter))

    new = {
        'user': user['user_id'],
        'fed_id': fed['fed_id'],
        'reason': reason
    }
    mongodb.fbanned_users.insert_one(new)

    # TODO(Notify all fedadmins)


@decorator.register(cmds='unfban')
@connection(admin=True, only_in_groups=True)
@get_user_and_fed_and_text_dec
@user_is_fed_admin
@get_strings_dec("feds")
async def un_fban_user(message, strings, status, chat_id, chat_title, user, fed, reason,
                       *args, **kwargs):
    from_id = message.from_user.id
    if user == BOT_ID:
        await message.reply(strings['unfban_self'])
        return

    check = mongodb.fbanned_users.find_one({'user': user['user_id'], 'fed_id': fed['fed_id']})
    if not check:
        await message.reply(strings['user_not_fbanned'].format(
                            user=await user_link_html(user['user_id'])))
        return

    fed_chats = mongodb.fed_groups.find({'fed_id': fed['fed_id']})

    text = strings['un_fbanned_header']
    text += strings['fbanned_fed'].format(fed=fed["fed_name"])
    text += strings['fbanned_fadmin'].format(fadmin=await user_link_html(from_id))
    text += strings['fbanned_user'].format(
        user=await user_link_html(user['user_id']) + f" (<code>{user['user_id']}</code>)")

    msg = await message.reply(text + strings['un_fbanned_process'].format(num=fed_chats.count()))

    counter = 0
    for chat in fed_chats:
        await asyncio.sleep(1)  # Do not slow down other updates
        try:
            await bot.unban_chat_member(
                chat['chat_id'],
                user['user_id']
            )
            counter += 1

        except Exception:
            continue

    mongodb.fbanned_users.delete_one({'_id': check['_id']})

    await msg.edit_text(text + strings['un_fbanned_done'].format(num=counter))


# Functions

@decorator.insurgent()
@get_strings_dec('feds')
async def fban_helper(event, strings):
    user = event.from_id
    chat = event.chat_id

    chat_fed = mongodb.fed_groups.find_one({'chat_id': chat})
    if not chat_fed:
        return

    if await is_user_admin(chat, user) is True:
        return

    if str(user) in WHITELISTED:
        return

    fed_id = chat_fed['fed_id']
    fed_name = mongodb.fed_list.find_one({'fed_id': fed_id})
    if not fed_name:
        return
    fed_name = fed_name['fed_name']

    is_banned = mongodb.fbanned_users.find_one({'user': user, 'fed_id': fed_id})
    if not is_banned:
        return

    banned_rights = ChatBannedRights(
        until_date=None,
        view_messages=True,
        send_messages=True,
        send_media=True,
        send_stickers=True,
        send_gifs=True,
        send_games=True,
        send_inline=True,
        embed_links=True,
    )

    try:
        ban = await event.client(EditBannedRequest(
            chat,
            user,
            banned_rights
        ))

        if ban:
            await event.respond(strings['fban_usr_rmvd'].format(
                fed=fed_name,
                user=await user_link(user),
                rsn=is_banned['reason']
            ))

    except Exception:
        pass


@decorator.ChatAction()
@get_strings_dec('feds')
async def fban_helper_2(event, strings):
    if event.user_joined is True or event.user_added is True:
        if hasattr(event.action_message.action, 'users'):
            from_id = event.action_message.action.users[0]
        else:
            from_id = event.action_message.from_id
    else:
        return  # ?

    chat = event.chat_id

    chat_fed = mongodb.fed_groups.find_one({'chat_id': chat})
    if not chat_fed:
        return

    if await is_user_admin(chat, from_id) is True:
        return

    if str(from_id) in WHITELISTED:
        return

    fed_id = chat_fed['fed_id']
    fed_name = mongodb.fed_list.find_one({'fed_id': fed_id})
    if not fed_name:
        return
    fed_name = fed_name['fed_name']

    is_banned = mongodb.fbanned_users.find_one({'user': from_id, 'fed_id': fed_id})
    if not is_banned:
        return

    banned_rights = ChatBannedRights(
        until_date=None,
        view_messages=True,
        send_messages=True,
        send_media=True,
        send_stickers=True,
        send_gifs=True,
        send_games=True,
        send_inline=True,
        embed_links=True,
    )

    try:
        ban = await event.client(EditBannedRequest(
            chat,
            from_id,
            banned_rights
        ))

        if ban:
            await event.respond(strings['fban_usr_rmvd'].format(
                fed=fed_name,
                user=await user_link(from_id),
                rsn=is_banned['reason']
            ))

    except Exception:
        pass
