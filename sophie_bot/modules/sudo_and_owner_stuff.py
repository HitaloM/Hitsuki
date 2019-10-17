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
import shutil
import asyncio
import os
import html
import requests
import datetime

from time import gmtime, strftime

from sophie_bot import SOPHIE_VERSION, tbot, decorator, mongodb, redis, logger, bot, db
from sophie_bot.modules.main import chat_term, term, convert_size
from sophie_bot.modules.notes import button_parser
from sophie_bot.modules.users import get_user_and_text, user_link_html
from sophie_bot.config import get_config_key


@decorator.register(cmds='allcommands', is_sudo=True)
async def all_commands_list(message):
    txt = ""
    for cmd in decorator.REGISTRED_COMMANDS:
        txt += "* /" + cmd + "\n"
    await message.reply(txt)


@decorator.register(cmds='ip', is_owner=True)
async def get_bot_ip(message):
    await message.reply(requests.get("http://ipinfo.io/ip").text)


@decorator.register(cmds="term", is_owner=True)
async def cmd_term(message):
    msg = await message.reply("Running...")
    command = str(message.text.split(" ", 1)[1])
    result = "<b>Shell:</b>\n"
    result += html.escape(await chat_term(message, command))
    await msg.edit_text(result)


@decorator.register(cmds="broadcast", is_owner=True)
async def broadcast(message):
    chats = mongodb.chat_list.find({})
    raw_text = message.get_args()
    text, buttons = button_parser(message.chat.id, raw_text)
    if len(buttons) == 0:
        buttons = None
    msg = await message.reply("Broadcasting to {} chats...".format(chats.count()))
    num_succ = 0
    num_fail = 0
    for chat in chats:
        try:
            await tbot.send_message(chat['chat_id'], text, buttons=buttons)
            num_succ = num_succ + 1
        except Exception as err:
            num_fail = num_fail + 1
            await msg.edit_text("Error:\n<code>{}</code>.\nBroadcasting will continues.".format(err))
            await asyncio.sleep(2)
            await msg.edit_text("Broadcasting to {} chats...".format(chats.count()))
    await msg.edit_text(
        "**Broadcast completed!** Message sended to <code>{}</code> chats successfully, \
<code>{}</code> didn't received message.".format(num_succ, num_fail))


@decorator.register(cmds="sbroadcast", is_owner=True)
async def sbroadcast(message):
    text = message.get_args()
    # Add chats to sbroadcast list
    chats = mongodb.chat_list.find({})
    mongodb.sbroadcast_list.drop()
    mongodb.sbroadcast_settings.drop()
    for chat in chats:
        mongodb.sbroadcast_list.insert_one({'chat_id': chat['chat_id']})
    mongodb.sbroadcast_settings.insert_one({
        'text': text,
        'all_chats': chats.count(),
        'recived_chats': 0
    })
    await message.reply(
        "Smart broadcast planned for <code>{}</code> chats".format(chats.count()))


@decorator.register(cmds="stopsbroadcast", is_owner=True)
async def stop_sbroadcast(message):
    old = mongodb.sbroadcast_settings.find_one({})
    mongodb.sbroadcast_list.drop()
    mongodb.sbroadcast_settings.drop()
    await message.reply("Smart broadcast stopped."
                        "It was sended to <code>{}</code> chats.".format(
                            old['recived_chats']))


# Check on smart broadcast
@decorator.insurgent()
async def check_message_for_smartbroadcast(event):
    chat_id = event.chat_id
    match = mongodb.sbroadcast_list.find_one({'chat_id': chat_id})
    if match:
        try:
            raw_text = mongodb.sbroadcast_settings.find_one({})['text']
            text, buttons = button_parser(event.chat_id, raw_text)
            if len(buttons) == 0:
                buttons = None
            await tbot.send_message(chat_id, text, buttons=buttons)
        except Exception as err:
            logger.error(err)
        mongodb.sbroadcast_list.delete_one({'chat_id': chat_id})
        old = mongodb.sbroadcast_settings.find_one({})
        num = old['recived_chats'] + 1
        mongodb.sbroadcast_settings.update(
            {'_id': old['_id']}, {
                'text': old['text'],
                'all_chats': old['all_chats'],
                'recived_chats': num
            }, upsert=False)


@decorator.register(cmds="backup", is_owner=True)
async def chat_backup(message):
    await do_backup(message.chat.id, message.message_id)


async def do_backup(chat_id, reply=False):
    await bot.send_message(chat_id, "Dumping the DB, please wait...", reply_to_message_id=reply)
    date = strftime("%Y-%m-%d_%H:%M:%S", gmtime())
    file_name = f"Backups/dump_{date}.7z"
    if not os.path.exists("Backups/"):
        os.mkdir("Backups/")
    await term(f"mongodump --uri \"{get_config_key('mongo_conn')}\" --out=Backups/tempbackup")

    # Let's also save Redis cache
    with open('Backups/tempbackup/redis_keys.json', 'w+') as f:
        keys = redis.keys()
        new = {}
        for key in keys:
            key_type = redis.type(key)
            if key_type == 'string':
                new[key] = redis.get(key)
            elif key_type == 'list':
                new[key] = list(redis.lrange(key, 0, -1))
        f.write(ujson.dumps(new, indent=2))

    # Copy config file
    shutil.copyfile('data/bot_conf.json', 'Backups/tempbackup/bot_conf.json')

    await bot.send_message(chat_id, "Compressing and uploading to Telegram...", reply_to_message_id=reply)
    password = get_config_key("backups_password")
    await term(f"cd Backups/tempbackup/; 7z a -mx9 ../../{file_name} * -p{password} -mhe=on")
    shutil.rmtree('Backups/tempbackup')

    if not os.path.exists(file_name):
        await bot.send_message(chat_id, "Error!", reply_to_message_id=reply)
        return

    text = "<b>Backup created!</b>"
    size = convert_size(os.path.getsize(file_name))
    text += f"\nBackup name: <code>{file_name}</code>"
    text += f"\nSize: <code>{size}</code>"
    await tbot.send_file(
        chat_id,
        file_name,
        reply_to=reply,
        caption=text,
        parse_mode="html"
    )


@decorator.register(cmds="purgecache", is_owner=True)
async def purge_caches(message):
    redis.flushdb()
    await message.reply("Redis cache was cleaned.")


@decorator.register(cmds="botstop", is_owner=True)
async def bot_stop(message):
    await message.reply("Goodbye...")
    exit(1)


@decorator.register(cmds="upload", is_owner=True)
async def upload_file(message):
    input_str = message.get_args()
    if os.path.exists(input_str):
        await message.reply("Processing ...")
        if os.path.exists(input_str):
            caption_rts = os.path.basename(input_str)
            myfile = open(input_str, 'rb')
            await tbot.send_file(
                message.chat.id,
                myfile,
                caption=caption_rts,
                force_document=False,
                allow_cache=False,
                reply_to=message.message_id
            )


@decorator.register(cmds="crash", is_owner=True)
async def crash(message):
    test = 2 / 0
    print(test)


@decorator.register(cmds="ppromote", is_sudo=True)
async def promote_to_gold(message):
    user, txt = await get_user_and_text(message)
    if not user:
        return

    user_id = user['user_id']

    check = mongodb.premium_users.find_one({'user_id': user_id})
    if check:
        await message.reply("This user already have gold rights!")
        return

    mongodb.premium_users.insert_one({'user_id': user_id})
    await message.reply(f"{await user_link_html(user_id)} now premium!")


@decorator.register(cmds="pdemote", is_sudo=True)
async def demote_from_gold(message):
    user, txt = await get_user_and_text(message)
    if not user:
        return

    user_id = user['user_id']

    check = mongodb.premium_users.find_one({'user_id': user_id})
    if not check:
        await message.reply("This user don't have gold rights!")
        return

    mongodb.premium_users.delete_one({'user_id': user_id})
    await message.reply(f"{await user_link_html(user_id)} demoted from premium users!")


@decorator.register(cmds="stats", is_sudo=True)
async def stats(message):
    text = f"<b>Sophie {SOPHIE_VERSION} stats</b>\n"
    text += "* <code>{}</code> total users, in <code>{}</code> chats\n".format(
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
    text += "* <code>{}</code> total notes\n".format(await db.notes.count_documents({}))
    text += "* <code>{}</code> total warns\n".format(await db.warns.count_documents({}))
    text += "* <code>{}</code> total gbanned users\n".format(await db.blacklisted_users.count_documents({}))
    text += "* <code>{}</code> chats in <code>{}</code> total feds, <code>{}</code> fbanned users\n".format(
        await db.fed_groups.count_documents({}),
        await db.fed_list.count_documents({}),
        await db.fbanned_users.count_documents({}))
    text += "* <code>{}</code> total crash happened in this week\n".format(
        await db.errors.count_documents({
            'date': {'$gte': datetime.datetime.now() - datetime.timedelta(days=7)}
        }))
    local_db = await db.command("dbstats")
    if 'fsTotalSize' in local_db:
        text += '* Database size is <code>{}</code>, free <code>{}</code>\n'.format(
            convert_size(local_db['dataSize']), convert_size(local_db['fsTotalSize'] - local_db['fsUsedSize']))
    else:
        text += '* Database size is <code>{}</code>, free <code>{}</code>\n'.format(
            convert_size(local_db['storageSize']), convert_size(536870912 - local_db['storageSize']))

    text += "* <code>{}</code> total keys in Redis database\n".format(len(redis.keys()))
    await message.reply(text)
