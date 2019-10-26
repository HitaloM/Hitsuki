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

import datetime
import html
import os

import requests

from sophie_bot import SOPHIE_VERSION
from sophie_bot.decorator import register, REGISTRED_COMMANDS
from sophie_bot.utils.logger import log
from sophie_bot.moduls import LOADED_MODULES
from sophie_bot.moduls.utils.term import chat_term
from sophie_bot.moduls.utils.covert import convert_size
from sophie_bot.services.mongo import db, mongodb
from sophie_bot.services.redis import redis
from sophie_bot.services.telethon import tbot
from sophie_bot.services.quart import quart


@register(cmds='allcommands', is_sudo=True)
async def all_commands_list(message):
    text = ""
    for cmd in REGISTRED_COMMANDS:
        text += "* /" + cmd + "\n"
    await message.reply(text)


@register(cmds='loadedmoduls', is_sudo=True)
async def all_modules_list(message):
    text = ""
    for module in LOADED_MODULES:
        text += "* " + module.__name__ + "\n"
    await message.reply(text)


@register(cmds='ip', is_owner=True)
async def get_bot_ip(message):
    await message.reply(requests.get("http://ipinfo.io/ip").text)


@register(cmds="term", is_owner=True)
async def cmd_term(message):
    msg = await message.reply("Running...")
    command = str(message.text.split(" ", 1)[1])
    text = "<b>Shell:</b>\n"
    text += html.escape(await chat_term(message, command))
    await msg.edit_text(text)


@register(cmds="sbroadcast", is_owner=True)
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


@register(cmds="stopsbroadcast", is_owner=True)
async def stop_sbroadcast(message):
    old = mongodb.sbroadcast_settings.find_one({})
    mongodb.sbroadcast_list.drop()
    mongodb.sbroadcast_settings.drop()
    await message.reply("Smart broadcast stopped."
                        "It was sended to <code>{}</code> chats.".format(
                            old['recived_chats']))


# Check on smart broadcast
# @decorator.insurgent()
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
            log.error(err)
        mongodb.sbroadcast_list.delete_one({'chat_id': chat_id})
        old = mongodb.sbroadcast_settings.find_one({})
        num = old['recived_chats'] + 1
        mongodb.sbroadcast_settings.update(
            {'_id': old['_id']}, {
                'text': old['text'],
                'all_chats': old['all_chats'],
                'recived_chats': num
            }, upsert=False)


@register(cmds="purgecache", is_owner=True)
async def purge_caches(message):
    redis.flushdb()
    await message.reply("Redis cache was cleaned.")


@register(cmds="botstop", is_owner=True)
async def bot_stop(message):
    await message.reply("Goodbye...")
    exit(1)


@register(cmds="upload", is_owner=True)
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


@register(cmds="crash", is_owner=True)
async def crash(message):
    test = 2 / 0
    print(test)


@register(cmds="stats", is_sudo=True)
async def stats(message):
    text = f"<b>Sophie {SOPHIE_VERSION} stats</b>\n"

    for module in [m for m in LOADED_MODULES if hasattr(m, '__stats__')]:
        text += await module.__stats__()

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
    text += "* <code>{}</code> total commands registred, in <code>{}</code> modules\n".format(
        len(REGISTRED_COMMANDS), len(LOADED_MODULES))

    await message.reply(text)


def html_white_text(text):
    text = f"<pre><font color=\"white\">{text}</font></pre>"
    return text


@quart.route('/stats')
async def is_gbanned():
    text = f"<b>Sophie {SOPHIE_VERSION} stats</b>\n"

    for module in [m for m in LOADED_MODULES if hasattr(m, '__stats__')]:
        text += await module.__stats__()

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
    text += "* <code>{}</code> total commands registred, in <code>{}</code> modules\n".format(
        len(REGISTRED_COMMANDS), len(LOADED_MODULES))

    return html_white_text(text)
