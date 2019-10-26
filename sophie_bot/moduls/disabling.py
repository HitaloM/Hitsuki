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

from .utils.disable import DISABLABLE_COMMANDS, disablable_dec
from .utils.language import get_strings_dec
from .utils.connections import chat_connection
from .utils.message import get_arg

from sophie_bot.decorator import register
from sophie_bot.services.mongo import db


@register(cmds="disablable")
@disablable_dec('disablable')
@get_strings_dec("disable")
async def list_disablable(message, strings):
    text = strings['disablable']
    for command in DISABLABLE_COMMANDS:
        text += f"* <code>/{command}</code>\n"
    await message.reply(text)


@register(cmds="disabled")
@chat_connection(only_groups=True)
@get_strings_dec("disable")
async def list_disabled(message, chat, strings):
    text = strings['disabled_list'].format(chat_name=chat['chat_title'])

    if await db.disabled_cmds.count_documents({'chat_id': chat['chat_id']}) < 1:
        await message.reply(strings['no_disabled_cmds'].format(chat_name=chat['chat_title']))
        return

    commands = db.disabled_cmds.find({'chat_id': chat['chat_id']})
    for command in await commands.to_list(length=300):
        text += f"* <code>/{command['command']}</code>\n"
    await message.reply(text)


@register(cmds="disable", is_admin=True)
@chat_connection(admin=True, only_groups=True)
@get_strings_dec("disable")
async def disable_command(message, chat, strings):
    cmd = get_arg(message).lower()
    if cmd[0] == '/' or cmd[0] == '!':
        cmd = cmd[1:]
    if cmd not in DISABLABLE_COMMANDS:
        await message.reply(strings["wot_to_disable"])
        return

    if await db.disabled_v2.find_one({'chat_id': chat['chat_id'], 'cmds': {'$in': [cmd]}}):
        await message.reply(strings['already_disabled'])
        return

    await db.disabled_v2.update_one(
        {'chat_id': chat['chat_id']},
        {"$addToSet": {'cmds': {'$each': [cmd]}}},
        upsert=True
    )

    await message.reply(strings["disabled"].format(
        cmd=cmd,
        chat_name=chat['chat_title']
    ))


@register(cmds="enable")
@chat_connection(admin=True, only_groups=True)
@get_strings_dec("disable")
async def enable_command(message, strings, status, chat_id, chat_title):
    if len(message.text.split(" ")) <= 1:
        await message.reply(strings["wot_to_enable"])
        return
    cmd = message.text.split(" ")[1].lower()
    if cmd[0] == '/' or cmd[0] == '!':
        cmd = cmd[1:]
    if cmd not in DISABLABLE_COMMANDS:
        await message.reply(strings["wot_to_enable"])
        return
    old = mongodb.disabled_cmds.find_one({
        "chat_id": chat_id,
        "command": cmd
    })
    if not old:
        await message.reply(strings["already_enabled"])
        return
    mongodb.disabled_cmds.delete_one({'_id': old['_id']})
    await message.reply(strings["enabled"].format(
        cmd=cmd, chat_name=chat_title))
