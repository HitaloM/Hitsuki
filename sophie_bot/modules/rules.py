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

from sophie_bot import decorator, mongodb
from sophie_bot.modules.connections import connection
from sophie_bot.modules.language import get_strings_dec
from sophie_bot.modules.users import user_admin_dec
from sophie_bot.modules.notes import send_note


@decorator.register(cmds="setrules")
@user_admin_dec
@connection(only_in_groups=True, admin=True)
@get_strings_dec("rules")
async def setrules(message, strings, status, chat_id, chat_title):
    note_to_find = message.text.split(" ", 1)[1]

    note = mongodb.notes.find_one({'chat_id': chat_id, 'name': note_to_find})

    if not note:
        return await message.reply(strings['cannot_find_note'])

    in_db = mongodb.rules.find_one({'chat_id': chat_id})

    if not in_db:
        mongodb.rules.insert_one({
            'chat_id': chat_id,
            'note': note_to_find
        })
    else:
        mongodb.rules.update_one({'chat_id': chat_id}, {
            "$set": {
                'note': note_to_find
            }
        })

    return await message.reply(strings['set_note'].format(note_to_find))


@decorator.register(cmds="rules")
@connection(only_in_groups=True)
@get_strings_dec("rules")
async def rules(message, strings, status, chat_id, chat_title):
    in_db = mongodb.rules.find_one({'chat_id': chat_id})

    if not in_db:
        return await message.reply(strings['didnt_set_note'])

    note_in_db = mongodb.notes.find_one({'chat_id': chat_id, 'name': in_db['note']})

    if not note_in_db:
        return await message.reply(strings['cannot_find_set_note'])

    await send_note(chat_id, chat_id, message.message_id, in_db['note'])


@decorator.register(cmds="delrules")
@user_admin_dec
@connection(only_in_groups=True, admin=True)
@get_strings_dec("rules")
async def delrules(message, strings, status, chat_id, chat_title):
    in_db = mongodb.rules.find_one({'chat_id': chat_id})

    if not in_db:
        return await message.reply(strings['havent_set_rules_note'])

    mongodb.rules.delete_one({'chat_id': chat_id})

    await message.reply(strings['success_remove_rules_note'].format(chat_title))
