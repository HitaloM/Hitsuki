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

import time

from aiogram.types.chat_permissions import ChatPermissions
from aiogram.utils.exceptions import NotEnoughRightsToRestrict

from telethon.tl.functions.channels import EditBannedRequest, GetParticipantRequest
from telethon.tl.types import ChatBannedRights, ChannelParticipantBanned
from telethon.errors.rpcerrorlist import ChatAdminRequiredError

import sophie_bot.modules.helper_func.bot_rights as bot_rights

from sophie_bot import BOT_ID, WHITELISTED, tbot, decorator, mongodb, bot
from sophie_bot.modules.helper_func.own_errors import NotEnoughRights
from sophie_bot.modules.connections import connection
from sophie_bot.modules.language import get_string, get_strings_dec
from sophie_bot.modules.users import (is_user_admin, user_admin_dec,
                                      get_user_and_text, user_link_html)


@decorator.command("ban")
@user_admin_dec
@bot_rights.ban_users()
@connection(admin=True, only_in_groups=True)
@get_strings_dec('bans')
async def ban(message, strings, status, chat_id, chat_title):
    user, reason = await get_user_and_text(message)
    if not user:
        return
    if await ban_user(message, user['user_id'], chat_id, None) is True:
        admin_str = await user_link_html(message.from_user.id)
        user_str = await user_link_html(user['user_id'])
        text = strings["user_banned"]
        if reason:
            text += strings["reason"].format(reason=reason)
        await message.reply(text.format(
            user=user_str, admin=admin_str, chat_name=chat_title),
            disable_web_page_preview=True
        )


@decorator.command("tban")
@user_admin_dec
@bot_rights.ban_users()
@connection(admin=True, only_in_groups=True)
@get_strings_dec('bans')
async def tban(message, strings, status, chat_id, chat_title):
    user, data = await get_user_and_text(message)
    if not user:
        return
    data = data.split(' ', 2)

    if len(data) > 1:
        reason = ' '.join(data[1:])
    else:
        reason = None

    time_val = data[0]

    if any(time_val.endswith(unit) for unit in ('m', 'h', 'd')):
        bantime, unit_str = await convert_time(message, time_val)

        if await ban_user(message, user['user_id'], chat_id, bantime) is True:
            admin_str = await user_link_html(message.from_user.id)
            user_str = await user_link_html(user['user_id'])
            text = "User {} banned by {} in {}!\n".format(user_str, admin_str, chat_title)
            text += "For <code>{}</code> {}\n".format(time_val[:-1], unit_str)
            if reason:
                text += "Reason: <code>{}</code>".format(reason)
            await message.reply(text, disable_web_page_preview=True)

    else:
        await message.reply(strings['invalid_time'])
        return


@decorator.command("kick")
@user_admin_dec
@bot_rights.ban_users()
@connection(admin=True, only_in_groups=True)
@get_strings_dec('bans')
async def kick(message, strings, status, chat_id, chat_title):
    user, text = await get_user_and_text(message)
    if not user:
        return
    if await kick_user(message, user['user_id'], chat_id) is True:
        admin_str = await user_link_html(message.from_user.id)
        user_str = await user_link_html(user['user_id'])
        text = strings["user_kicked"]
        await message.reply(text.format(admin=admin_str, user=user_str, chat_name=chat_title))


@decorator.command("unban")
@user_admin_dec
@bot_rights.ban_users()
@connection(admin=True, only_in_groups=True)
@get_strings_dec("bans")
async def unban(message, strings, status, chat_id, chat_title):
    user, text = await get_user_and_text(message)
    if not user:
        return
    if await unban_user(message, user['user_id'], chat_id):
        admin_str = await user_link_html(message.from_user.id)
        user_str = await user_link_html(user['user_id'])
        text = strings["user_unbanned"]

        if gbanned := mongodb.blacklisted_users.find_one({'user_id': user['user_id']}):
            text += strings["user_gbanned"].format(reason=gbanned['reason'])
            mongodb.blacklisted_users.update_one(
                {'_id': gbanned['_id']},
                {"$addToSet": {'force_unbanned_chats': {'$each': [chat_id]}}},
                upsert=False
            )

        await message.reply(text.format(admin=admin_str, user=user_str, chat_name=chat_title))


@decorator.command("mute")
@user_admin_dec
@bot_rights.ban_users()
@connection(admin=True, only_in_groups=True)
@get_strings_dec("bans")
async def muter(message, strings, status, chat_id, chat_title):
    user, text = await get_user_and_text(message)
    if not user:
        return
    if await mute_user(message, user['user_id'], chat_id, None):
        admin_str = await user_link_html(message.from_user.id)
        user_str = await user_link_html(user['user_id'])
        text = strings["user_mooted"]
        await message.reply(text.format(admin=admin_str, user=user_str, chat_name=chat_title))


@decorator.command("unmute")
@user_admin_dec
@bot_rights.ban_users()
@connection(admin=True, only_in_groups=True)
@get_strings_dec("bans")
async def unmute(message, strings, status, chat_id, chat_title):
    user, text = await get_user_and_text(message)
    if not user:
        return
    if await unmute_user(message, user['user_id'], chat_id):
        admin_str = await user_link_html(message.from_user.id)
        user_str = await user_link_html(user['user_id'])
        text = strings["user_unmooted"]
        await message.reply(text.format(admin=admin_str, user=user_str, chat_name=chat_title))


@decorator.command("kickme")
@bot_rights.ban_users()
@get_strings_dec("bans")
async def kickme(message, strings):
    user = message.from_user.id
    chat = message.chat.id

    if await ban_user(message, user, chat, None) is True:
        await message.reply(strings["kickme_success"])


@decorator.command("tmute")
@user_admin_dec
@bot_rights.ban_users()
@connection(admin=True, only_in_groups=True)
@get_strings_dec("bans")
async def tmute(message, strings, status, chat_id, chat_title):
    user, data = await get_user_and_text(message)
    if not user:
        return
    data = data.split(' ', 2)
    time_val = data[0]

    if any(time_val.endswith(unit) for unit in ('m', 'h', 'd')):
        mutetime, unit_str = await convert_time(message, time_val)

        if await mute_user(message, user['user_id'], chat_id, mutetime) is True:
            admin_str = await user_link_html(message.from_user.id)
            user_str = await user_link_html(user['user_id'])
            await message.reply(strings["tmute_sucess"].format(
                admin=admin_str, user=user_str,
                time=time_val[:-1], unit=unit_str))
    else:
        await message.reply(strings['invalid_time'])
        return


async def ban_user(message, user_id, chat_id, time_val, no_msg=False):
    real_chat_id = message.chat.id

    if str(user_id) in WHITELISTED:
        if no_msg is False:
            await message.reply("This user is whitelisted")
        return

    if user_id == BOT_ID:
        if no_msg is False:
            await message.reply(get_string("bans", "bot_cant_be_banned", real_chat_id))
        return False
    if await is_user_admin(chat_id, user_id) is True:
        if no_msg is False:
            await message.reply(get_string("bans", "user_admin_ban", real_chat_id))
        return False

    banned_rights = ChatBannedRights(
        until_date=time_val,
        view_messages=True
    )

    try:
        await tbot(EditBannedRequest(chat_id, user_id, banned_rights))
    except ChatAdminRequiredError:
        raise NotEnoughRights('ban')

    return True


async def kick_user(message, user_id, chat_id, no_msg=False):
    real_chat_id = message.chat.id

    if user_id == BOT_ID:
        if no_msg is False:
            await message.reply(get_string("bans", "bot_cant_be_kicked", real_chat_id))
        return False
    if await is_user_admin(chat_id, user_id) is True:
        if no_msg is False:
            await message.reply(get_string("bans", "user_admin_kick", real_chat_id))
        return False

    try:
        await tbot.kick_participant(chat_id, user_id)
        await bot.unban_chat_member(chat_id, user_id)
    except NotEnoughRightsToRestrict:
        raise NotEnoughRights('kick')

    return True


async def unban_user(message, user_id, chat_id):
    real_chat_id = message.chat.id

    if user_id == BOT_ID:
        await message.reply(get_string("bans", "bot_cant_be_unbanned", real_chat_id))
        return False
    try:
        peep = await tbot(GetParticipantRequest(chat_id, user_id))

        if not isinstance(peep.participant, ChannelParticipantBanned):
            await message.reply(get_string('bans', 'usernt_banned', real_chat_id))
            return False
    except Exception:
        pass

    await bot.unban_chat_member(chat_id, user_id)
    return True


async def mute_user(message, user_id, chat_id, time_val, no_msg=False):
    real_chat_id = message.chat.id
    if str(user_id) in WHITELISTED:
        await message.reply("This user is whitelisted")
        return

    if user_id == BOT_ID:
        await message.reply(get_string("bans", "bot_cant_be_muted", real_chat_id))
        return False
    if await is_user_admin(chat_id, user_id) is None:
        await message.reply(get_string("bans", "user_admin_mute", real_chat_id))
        return False

    try:
        await bot.restrict_chat_member(
            chat_id,
            user_id,
            permissions=ChatPermissions(can_send_messages=False, until_date=time_val)
        )
    except NotEnoughRightsToRestrict:
        raise NotEnoughRights('mute')

    return True


async def unmute_user(message, user_id, chat_id):
    real_chat_id = message.chat.id

    if user_id == BOT_ID:
        await message.reply(get_string("bans", "bot_cant_be_unmuted", real_chat_id))
        return False
    if await is_user_admin(chat_id, user_id) is None:
        await message.reply(get_string("bans", "user_admin_unmute", real_chat_id))
        return False

    try:
        await bot.restrict_chat_member(
            chat_id,
            user_id,
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True
        )
    except NotEnoughRightsToRestrict:
        raise NotEnoughRights('unmute')

    return True


async def convert_time(event, time_val):
    if hasattr(event, 'chat_id'):
        chat_id = event.chat_id
    elif hasattr(event, 'chat'):
        chat_id = event.chat.id

    if any(time_val.endswith(unit) for unit in ('m', 'h', 'd')):
        time_num = time_val[:-1]
        unit = time_val[-1]
        if unit == 'm':
            mutetime = int(time.time() + int(time_num) * 60)
            unit_str = 'minutes'
        elif unit == 'h':
            mutetime = int(time.time() + int(time_num) * 60 * 60)
            unit_str = 'hours'
        elif unit == 'd':
            mutetime = int(time.time() + int(time_num) * 24 * 60 * 60)
            unit_str = 'days'
        else:
            return await event.reply(get_string("bans", "time_var_incorrect", chat_id))

        return mutetime, unit_str
