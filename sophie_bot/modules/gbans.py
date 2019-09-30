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

import html

from time import gmtime, strftime
import asyncio

from flask import jsonify, request

from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights

from aiogram.utils.exceptions import BadRequest

from sophie_bot import CONFIG, SUDO, WHITELISTED, decorator, logger, mongodb, bot, flask
from sophie_bot.modules.language import get_string, get_strings_dec
from sophie_bot.modules.users import user_link, aio_get_user, user_link_html, is_user_admin
from sophie_bot.modules.helper_func.decorators import need_args_dec
import sophie_bot.modules.helper_func.bot_rights as bot_rights


@decorator.command("gban", is_sudo=True)
@need_args_dec()
async def blacklist_user(message):
    user, reason = await aio_get_user(message)
    if not user:
        return

    user_id = int(user['user_id'])
    sudo_admin = message.from_user.id

    if user_id in WHITELISTED:
        await message.reply("You can't blacklist a Whitelisted user")
        return

    if not reason:
        await message.reply("You can't blacklist user without a reason!")
        return

    reason = html.escape(reason)

    date = strftime("%Y-%m-%d %H:%M:%S", gmtime())

    text = "<b>New blacklisted user!</b>"
    text += "\nUser: " + await user_link_html(user_id)
    text += "\nID: <code>" + str(user_id) + '</code>'
    text += "\nDate: <code>" + date + '</code>'

    if old := mongodb.blacklisted_users.find_one({'user_id': user_id}):
        mongodb.blacklisted_users.update_one({'_id': old['_id']}, {"$set": {'reason': reason}}, upsert=False)

        text += f"\nOld reason: <code>{old['reason']}</code>"
        text += f"\nNew reason: <code>{reason}</code>"

        await message.reply(text)
        if CONFIG['advanced']['gbans_channel_enabled'] is True:
            await bot.send_message(CONFIG['advanced']['gbans_channel'], text)
        return

    text += "\nBy: " + await user_link_html(sudo_admin) + f" ({sudo_admin})"
    text += "\nReason: <code>" + reason + '</code>'

    msg = await message.reply(text + "\nStatus: <b>Blacklisting user...</b>")

    gbanned_chats = []
    if 'chats' not in user or not user['chats']:
        try:
            await bot.kick_chat_member(message.chat.id, user_id)
            gbanned_chats += message.chat.id
            ttext = text + "\nStatus: <b>User banned only in this chat</b>"
            await msg.edit_text(ttext)
        except Exception:
            pass

    for chat_id in user['chats']:
        await asyncio.sleep(0.2)
        try:
            await bot.kick_chat_member(chat_id, user_id)
            gbanned_chats.append(int(chat_id))
        except BadRequest:
            pass

    new = {
        'user_id': user_id,
        'date': date,
        'reason': reason,
        'by': sudo_admin,
        'gbanned_chats': gbanned_chats
    }

    mongodb.blacklisted_users.insert_one(new)

    if len(gbanned_chats) > 0:
        ttext = text + f"\nStatus: <b>Done, user banned in {len(gbanned_chats)}/{len(user['chats'])} chats.</b>"
    else:
        ttext = text + "\nStatus: <b>User not banned in any chat, but added in blacklist</b>"

    await msg.edit_text(ttext)
    if CONFIG['advanced']['gbans_channel_enabled'] is True:
        await bot.send_message(CONFIG['advanced']['gbans_channel'], ttext)


@decorator.command("ungban")
async def un_blacklist_user(message):
    if message.from_user.id not in SUDO:
        return
    chat_id = message.chat.id
    user, txt = await aio_get_user(message)
    if not user:
        return

    user_id = user['user_id']

    checker = 0

    # Unban user from previously banned chats
    if gbanned := mongodb.blacklisted_users.find_one({'user_id': user_id}):
        if 'gbanned_chats' in gbanned:
            for chat in gbanned['gbanned_chats']:
                await bot.unban_chat_member(chat, user_id)
                checker += 1
    else:
        await message.reply(f"{await user_link_html(user_id)} isn't blacklisted! Do you wanna change it? 😏")
        return

    mongodb.blacklisted_users.delete_one({'_id': gbanned['_id']})
    text = "<b>New un-blacklisted user!</b>"
    text += "\nUser: " + await user_link_html(user_id)
    text += f"\nID: <code>{user_id}</code>"
    text += f"\nDate: <code>{strftime('%Y-%m-%d %H:%M:%S', gmtime())}</code>"
    text += "\nBy: " + await user_link_html(message.from_user.id) + f" ({message.from_user.id})"
    if checker > 0:
        text += f"\nStatus: <b>unbanned in {checker}/{len(user['chats'])} chats</b>"
    else:
        text += "\nStatus: <b>User not unbanned in any chat, but removed from DB</b>"

    await message.reply(text)

    if CONFIG['advanced']['gbans_channel_enabled'] is True:
        await bot.send_message(CONFIG['advanced']['gbans_channel'], text)


@decorator.AioBotDo()
@bot_rights.ban_users()
@get_strings_dec('gbans')
async def gban_trigger(message, strings, **kwargs):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if await is_user_admin(chat_id, user_id):
        return

    if not (gbanned := mongodb.blacklisted_users.find_one({'user_id': user_id})):
        return

    if chat_id in gbanned['force_unbanned_chats']:
        return

    await bot.kick_chat_member(chat_id, user_id)

    mongodb.blacklisted_users.update_one(
        {'_id': gbanned['_id']},
        {"$set": {'gbanned_chats': gbanned['gbanned_chats'].remove(chat_id)}},
        upsert=False
    )
    await event.reply(strings['user_is_blacklisted'].format(
        await user_link_html(user_id), gbanned['reason']))


@decorator.AioWelcome()
@bot_rights.ban_users()
@get_strings_dec('gbans')
async def gban_helper_welcome(message, strings, **kwargs):
    if hasattr(event.action_message.action, 'users'):
        user_id = event.action_message.action.users[0]
    else:
        user_id = event.action_message.from_id

    if await is_user_admin(chat_id, user_id):
        return

    if not (gbanned := mongodb.blacklisted_users.find_one({'user_id': user_id})):
        return

    if chat_id in gbanned['force_unbanned_chats']:
        return

    await bot.kick_chat_member(chat_id, user_id)

    mongodb.blacklisted_users.update_one(
        {'_id': gbanned['_id']},
        {"$set": {'gbanned_chats': gbanned['gbanned_chats'].remove(chat_id)}},
        upsert=False
    )
    await event.reply(strings['user_is_blacklisted'].format(
        await user_link_html(user_id), gbanned['reason']))


@flask.route('/api/is_user_gbanned/<user_id>')
def is_gbanned(user_id: int):
    print(request.headers)
    gbanned = mongodb.blacklisted_users.find_one({'user_id': int(user_id)})
    if not gbanned:
        data = {'user_id': int(user_id), 'gbanned': False}
        return jsonify(data)
    data = mongodb.user_list.find_one({'user_id': user_id})
    if not data:
        data = {}

    data.update(gbanned)
    del data['_id']
    return jsonify(data)
