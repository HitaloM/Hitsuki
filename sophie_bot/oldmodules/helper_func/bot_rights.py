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

from telethon.tl.functions.channels import GetParticipantRequest

from sophie_bot import BOT_ID, tbot
from sophie_bot.modules.language import get_string


# Help
# change_info = rights.change_info
# post_messages = rights.post_messages
# edit_messages = rights.edit_messages
# delete_messages = rights.delete_messages
# ban_users = rights.ban_users invite_users = rights.invite_users
# pin_messages = rights.pin_messages
# add_admins = rights.add_admins


async def get_bot_rights(chat_id):
	try:
		bot_req = await tbot(GetParticipantRequest(channel=chat_id, user_id=BOT_ID))
	except Exception:
		return False
	if bot_req and hasattr(bot_req, 'participant') and hasattr(bot_req.participant, 'admin_rights'):
		return bot_req.participant.admin_rights
	return False


def change_info():
	def decorator(func, *dec_args, **dev_kwargs):
		chat_id = None

		async def wrapped_1(event):
			if hasattr(event, 'chat_id'):
				chat_id = event.chat_id
			elif hasattr(event, 'chat'):
				chat_id = event.chat.id
			else:
				chat_id = None

			rights = await get_bot_rights(chat_id)
			if rights is not False and rights.change_info and rights.change_info:
				return await(func(event, *dec_args, **dev_kwargs))
			else:
				await event.reply(get_string("bot_rights", "change_info", chat_id))
				return

		return wrapped_1

	return decorator


def post_messages():
	def decorator(func, *dec_args, **dev_kwargs):
		chat_id = None

		async def wrapped_1(event):
			if hasattr(event, 'chat_id'):
				chat_id = event.chat_id
			elif hasattr(event, 'chat'):
				chat_id = event.chat.id

			rights = await get_bot_rights(chat_id)
			if rights is not False and rights.post_messages and rights.post_messages:
				return await(func(event, *dec_args, **dev_kwargs))
			else:
				# No answer if don't have rights
				return

		return wrapped_1

	return decorator


def edit_messages():
	def decorator(func, *dec_args, **dev_kwargs):
		async def wrapped_1(event):
			chat_id = None
			if hasattr(event, 'chat_id'):
				chat_id = event.chat_id
			elif hasattr(event, 'chat'):
				chat_id = event.chat.id

			rights = await get_bot_rights(chat_id)
			if rights is not False and rights.edit_messages and rights.edit_messages:
				return await(func(event, *dec_args, **dev_kwargs))
			else:
				await event.reply(get_string("bot_rights", "edit_messages", chat_id))
				return

		return wrapped_1

	return decorator


def delete_messages():
	def decorator(func, *dec_args, **dev_kwargs):
		async def wrapped_1(event):
			chat_id = None
			if hasattr(event, 'chat_id'):
				chat_id = event.chat_id
			elif hasattr(event, 'chat'):
				chat_id = event.chat.id

			rights = await get_bot_rights(chat_id)
			if rights is not False and rights.delete_messages and rights.delete_messages:
				return await(func(event, *dec_args, **dev_kwargs))
			else:
				await event.reply(get_string("bot_rights", "delete_messages", chat_id))
				return

		return wrapped_1

	return decorator


def ban_users():
	def decorator(func, *dec_args, **dev_kwargs):
		async def wrapped_1(event):
			chat_id = None
			if hasattr(event, 'chat_id'):
				chat_id = event.chat_id
			elif hasattr(event, 'chat'):
				chat_id = event.chat.id

			rights = await get_bot_rights(chat_id)
			if rights is not False and rights.ban_users and rights.ban_users:
				return await(func(event, *dec_args, **dev_kwargs))
			else:
				await event.reply(get_string("bot_rights", "ban_users", chat_id))
				return

		return wrapped_1

	return decorator


def pin_messages():
	def decorator(func, *dec_args, **dev_kwargs):
		async def wrapped_1(event):
			chat_id = None
			if hasattr(event, 'chat_id'):
				chat_id = event.chat_id
			elif hasattr(event, 'chat'):
				chat_id = event.chat.id

			rights = await get_bot_rights(chat_id)
			if rights is not False and rights.pin_messages and rights.pin_messages:
				return await(func(event, *dec_args, **dev_kwargs))
			else:
				await event.reply(get_string("bot_rights", "pin_messages", chat_id))
				return

		return wrapped_1

	return decorator


def add_admins():
	def decorator(func, *dec_args, **dev_kwargs):
		async def wrapped_1(event):
			chat_id = None
			if hasattr(event, 'chat_id'):
				chat_id = event.chat_id
			elif hasattr(event, 'chat'):
				chat_id = event.chat.id

			rights = await get_bot_rights(chat_id)
			if rights is not False and rights.add_admins and rights.add_admins:
				return await(func(event, *dec_args, **dev_kwargs))
			else:
				await event.reply(get_string("bot_rights", "add_admins", chat_id))
				return

		return wrapped_1

	return decorator
