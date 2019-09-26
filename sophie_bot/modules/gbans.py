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

from time import gmtime, strftime
import asyncio

from flask import jsonify, request

from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights

from sophie_bot import CONFIG, SUDO, WHITELISTED, decorator, logger, mongodb, bot, flask
from sophie_bot.modules.language import get_string, get_strings_dec
from sophie_bot.modules.users import user_link, aio_get_user, user_link_html
from sophie_bot.modules.helper_func.decorators import need_args_dec


GBANNED_RIGHTS = ChatBannedRights(
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


@decorator.command("gban")
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
        await message.reply("You can't blacklist user without a reason blyat!")
        return

    reason = reason.replace('<', '&lt;')

    date = strftime("%Y-%m-%d %H:%M:%S", gmtime())

    text = "{} <b>blacklisted!</b>".format(await user_link_html(user_id))
    text += "\nID: <code>" + str(user_id) + '</code>'
    text += "\nBy: " + await user_link_html(sudo_admin)
    text += "\nDate: <code>" + date + '</code>'
    text += "\nReason: <code>" + reason + '</code>'

    old = mongodb.blacklisted_users.find_one({'user_id': user_id})
    if old:
        new = {
            'user_id': user_id,
            'date': old['date'],
            'by': old['by'],
            'reason': reason
        }
        mongodb.blacklisted_users.update_one({'_id': old['_id']}, {"$set": new}, upsert=False)
        await message.reply("This user already blacklisted! I'll update the reason.")
        return

    msg = await message.reply(text + "\nStatus: <b>Gbanning...</b>")

    new = {
        'user_id': user_id,
        'date': date,
        'reason': reason,
        'by': sudo_admin
    }

    mongodb.blacklisted_users.insert_one(new)

    gbanned_ok = 0
    if 'chats' not in user or not user['chats']:
        try:
            await bot.kick_chat_member(message.chat.id, user_id)
        except Exception:
            pass
        ttext = text + "\nStatus: <b>User not banned in any chat, but added in blacklist</b>"
        await msg.edit_text(ttext)
        if CONFIG['advanced']['gbans_channel_enabled'] is True:
            await bot.send_message(CONFIG['advanced']['gbans_channel'], ttext)
            return

    for chat in user['chats']:
        await asyncio.sleep(0.2)
        try:
            await bot.kick_chat_member(chat, user_id)
            gbanned_ok += 1
        except Exception:
            continue

    ttext = text + "\nStatus: <b>Done, user gbanned in {}/{} chats.</b>".format(
        gbanned_ok, len(user['chats']))
    await msg.edit_text(ttext)
    if CONFIG['advanced']['gbans_channel_enabled'] is True:
        await bot.send_message(CONFIG['advanced']['gbans_channel'], ttext)


@decorator.command("ungban")
async def un_blacklist_user(message):
    if message.from_user.id not in SUDO:
        return
    chat_id = message.chat.id
    user_id, txt = await aio_get_user(message)
    if not user_id:
        return

    user_id = user_id['user_id']

    checker = 0

    try:
        precheck = mongodb.gbanned_groups.find({'user_id': user_id})
        if precheck:
            chats = mongodb.gbanned_groups.find({'user_id': user_id})
        else:
            chats = chat_id
        for chat in chats:
            await bot.unban_chat_member(chat['chat_id'], user_id)
        checker += 1
    except Exception:
        pass

    old = mongodb.blacklisted_users.find_one({'user_id': user_id})
    if not old:
        await message.reply("This user isn't blacklisted!")
        return
    mongodb.blacklisted_users.delete_one({'_id': old['_id']})
    text = "Sudo {} unblacklisted {}.\nStatus: <b>unbanned in {} chats</b>".format(
        await user_link_html(message.from_user.id), await user_link_html(user_id), checker)
    await message.reply(text)

    if CONFIG['advanced']['gbans_channel_enabled'] is True:
        await bot.send_message(CONFIG['advanced']['gbans_channel'], text)


@decorator.insurgent()
async def gban_trigger(event):
    user_id = event.from_id

    K = mongodb.blacklisted_users.find_one({'user_id': user_id})
    if K:
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
            ban = await event.client(
                EditBannedRequest(
                    event.chat_id,
                    user_id,
                    banned_rights
                )
            )

            if ban:
                mongodb.gbanned_groups.insert_one({'user_id': user_id, 'chat_id': event.chat_id})
                await event.reply(get_string("gbans", "user_is_blacklisted", event.chat_id).format(
                                  await user_link(user_id), K['reason']))

        except Exception:
            pass


@decorator.ChatAction()
@get_strings_dec('gbans')
async def gban_helper_2(event, strings):
    if event.user_joined is True or event.user_added is True:
        await asyncio.sleep(2)  # Sleep 2 seconds before check user to allow Simon gban user
        if hasattr(event.action_message.action, 'users'):
            from_id = event.action_message.action.users[0]
        else:
            from_id = event.action_message.from_id

        K = mongodb.blacklisted_users.find_one({'user_id': from_id})
        if not K:
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
            ban = await event.client(
                EditBannedRequest(
                    event.chat_id,
                    from_id,
                    banned_rights
                )
            )

            if ban:
                mongodb.gbanned_groups.insert_one({'user_id': from_id, 'chat_id': event.chat_id})
                await event.reply(
                    strings['user_is_blacklisted'].format(
                        user=await user_link(from_id),
                        rsn=K['reason']
                    ))

        except Exception as err:
            logger.info(f'Error on gbanning {from_id} in {event.chat_id} \n {err}')
            pass


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
