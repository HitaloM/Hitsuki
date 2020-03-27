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
