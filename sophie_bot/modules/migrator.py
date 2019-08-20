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

from aiogram import types

from sophie_bot import mongodb, dp, bot


@dp.message_handler(content_types=types.ContentTypes.MIGRATE_TO_CHAT_ID)
async def migrator(message):
    old_id = message.chat.id
    new_id = message.migrate_to_chat_id

    # Migrating data
    for collection in mongodb.collection_names():
        for document in mongodb[collection].find({'chat_id': old_id}):
            mongodb[collection].update_many(
                {'_id': document['_id']},
                {'$set': {'chat_id': new_id}}
            )

    text = "<b>Chat migration</b>"
    text += "\nThis chat was migrated!"
    text += f"\nOld ID : <code>{old_id}</code>"
    text += f"\nNew ID : <code>{new_id}</code>"
    text += "\nData migrated successfully."

    await bot.send_message(new_id, text)
