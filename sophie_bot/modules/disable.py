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

from sophie_bot import SUDO, decorator, mongodb
from sophie_bot.modules.connections import connection
from sophie_bot.modules.language import get_strings_dec
from sophie_bot.modules.users import user_admin_dec

global DISABLABLE_COMMANDS
DISABLABLE_COMMANDS = []


def disablable_dec(command):
    if command not in DISABLABLE_COMMANDS:
        DISABLABLE_COMMANDS.append(command)

    def wrapped(func):
        async def wrapped_1(event, *args, **kwargs):

            if hasattr(event, 'chat_id'):
                chat_id = event.chat_id
            elif hasattr(event, 'chat'):
                chat_id = event.chat.id

            if hasattr(event, 'from_id'):
                user_id = event.from_id
            elif hasattr(event, 'from_user'):
                user_id = event.from_user.id

            check = mongodb.disabled_cmds.find_one({
                "chat_id": chat_id,
                "command": command
            })
            if check and user_id not in SUDO:
                return
            return await func(event, *args, **kwargs)
        return wrapped_1
    return wrapped


@decorator.register(cmds="disablable")
@disablable_dec('disablable')
@get_strings_dec("disable")
async def list_disablable(message, strings, **kwargs):
    text = strings['disablable']
    for command in DISABLABLE_COMMANDS:
        text += f"* <code>/{command}</code>\n"
    await message.reply(text)


@decorator.register(cmds="disabled")
@connection(only_in_groups=True)
@get_strings_dec("disable")
async def list_disabled(message, strings, status, chat_id, chat_title):
    text = strings['disabled_list'].format(chat_name=chat_title)
    commands = mongodb.disabled_cmds.find({'chat_id': chat_id})
    for command in commands:
        text += f"* <code>/{command['command']}</code>\n"
    await message.reply(text)


@decorator.register(cmds="disable")
@user_admin_dec
@connection(admin=True, only_in_groups=True)
@get_strings_dec("disable")
async def disable_command(message, strings, status, chat_id, chat_title):
    if len(message.text.split(" ")) <= 1:
        await message.reply(strings["wot_to_disable"])
        return
    cmd = message.text.split(" ")[1].lower()
    if cmd[0] == '/' or cmd[0] == '!':
        cmd = cmd[1:]
    if cmd not in DISABLABLE_COMMANDS:
        await message.reply(strings["wot_to_disable"])
        return
    new = {
        "chat_id": chat_id,
        "command": cmd
    }
    old = mongodb.disabled_cmds.find_one(new)
    if old:
        await message.reply(strings['already_disabled'])
        return
    mongodb.disabled_cmds.insert_one(new)
    await message.reply(strings["disabled"].format(
        cmd=cmd, chat_name=chat_title))


@decorator.register(cmds="enable")
@user_admin_dec
@connection(admin=True, only_in_groups=True)
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
