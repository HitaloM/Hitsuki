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

import base64
import bz2
import difflib
import re
from time import gmtime, strftime

from aiogram import types
from sophie_bot.modules.connections import connection, get_conn_chat
from sophie_bot.modules.disable import disablable_dec
from sophie_bot.modules.helper_func.decorators import need_args_dec
from telethon import errors, utils
from telethon.tl.functions.users import GetFullUserRequest

from sophie_bot import tbot, decorator, logger, dp, db, bot
from sophie_bot.modules.language import get_string, get_strings_dec
from sophie_bot.modules.users import (
	check_group_admin,
	user_admin_dec, user_link,
	add_user_to_db, user_link_html
)

RESTRICTED_SYMBOLS = ['**', '__', '`']


@decorator.register(cmds="owo")
async def test(message, **kwargs):
	print(await bot.get_chat_administrators(message.chat.id))


@decorator.t_command("save", word_arg=True)
@user_admin_dec
@connection(admin=True)
@get_strings_dec("notes")
async def save_note(event, strings, status, chat_id, chat_title):
	note_name = event.pattern_match.group(1)
	for sym in RESTRICTED_SYMBOLS:
		if sym in note_name:
			await event.reply(strings["notename_cant_contain"].format(sym))
			return
	if note_name[0] == "#":
		note_name = note_name[1:]

	note_name = note_name.lower()
	file_id = None
	prim_text = ""
	if len(event.message.text.split(" ")) > 2:
		prim_text = event.text.partition(note_name)[2]
	if event.message.reply_to_msg_id:
		msg = await event.get_reply_message()
		if not msg:
			await event.reply(strings["bot_msg"])
			return
		note_text = msg.message
		if prim_text:
			note_text += prim_text
		if hasattr(msg.media, 'photo'):
			file_id = utils.pack_bot_file_id(msg.media)
		if hasattr(msg.media, 'document'):
			file_id = utils.pack_bot_file_id(msg.media)
	else:
		note_text = prim_text

	status = strings["saved"]
	old = await db.notes.find_one({'chat_id': chat_id, "name": note_name})
	date = strftime("%Y-%m-%d %H:%M:%S", gmtime())
	created_date = date
	creator = None
	encrypted = "particle-v1"
	if old:
		if 'created' in old:
			created_date = old['created']
		if 'creator' in old:
			creator = old['creator']
		status = strings["updated"]

	if not creator:
		creator = event.from_id

	h = re.search(r"(\[encryption:(particle|no)\])", note_text)
	if h:
		note_text = note_text.replace(h.group(1), "")
		format_raw = h.group(2).lower()
		if format_raw == 'no':
			encrypted = False
		elif format_raw == 'particle':
			encrypted = "particle-v1"

	if encrypted == "particle-v1":
		note_text = base64.urlsafe_b64encode(bz2.compress(note_text.encode()))

	new = ({
		'chat_id': chat_id,
		'name': note_name,
		'text': note_text,
		'date': date,
		'created': created_date,
		'updated_by': event.from_id,
		'creator': creator,
		'file_id': file_id,
		'encrypted': encrypted
	})

	await db.notes.update_one({'_id': old['_id']}, {"$set": new}, upsert=True)

	text = strings["note_saved_or_updated"].format(
		note_name=note_name, status=status, chat_title=chat_title)

	if encrypted is False:
		text += strings["note_not_encrypted"]
		text += strings["you_can_get_note"].format(name=note_name)
	elif encrypted == "particle-v1":
		text += strings["you_can_get_note"].format(name=note_name)

	await event.reply(text)


@decorator.register(cmds="clear")
@user_admin_dec
@connection(admin=True)
@get_strings_dec("notes")
async def clear_note(message, strings, status, chat_id, chat_title):
	note_name = message.get_args().split(" ")[0].lower()
	if not note_name:
		return await message.reply(strings["no_note"])

	if await db.notes.delete_one({'chat_id': chat_id, "name": note_name}):
		text = strings["note_removed"].format(
			note_name=note_name, chat_name=chat_title)
	else:
		text = strings["cant_find_note"].format(chat_name=chat_title)
	await message.reply(text)


@decorator.register(cmds="noteinfo")
@user_admin_dec
@connection(admin=True)
@get_strings_dec("notes")
async def note_info(message, strings, status, chat_id, chat_title):
	note_name = message.get_args()
	note = await db.notes.find_one({'chat_id': chat_id, "name": note_name})
	if not note:
		text = strings["cant_find_note"]
	else:
		text = strings["note_info_title"]
		text += strings["note_info_note"].format(note_name=note_name)
		text += strings["note_info_created"].format(
			data=note['created'], user=await user_link_html(note['creator']))
		text += strings["note_info_updated"].format(
			data=note['date'], user=await user_link_html(note['updated_by']))

	await message.reply(text)


@decorator.register(cmds=["notes", "saved"])
@disablable_dec("notes")
@connection()
@get_strings_dec("notes")
async def list_notes(message, strings, status, chat_id, chat_title):
	notes = db.notes.find({'chat_id': chat_id}).sort("name", 1)
	text = strings["notelist_header"].format(chat_name=chat_title)
	if notes == 0:
		text = strings["notelist_no_notes"]
	else:
		for note in await notes.to_list(length=300):
			text += "- <code>#{}</code>\n".format(note['name'])
	await message.reply(text)


async def send_note(chat_id, group_id, msg_id, note_name,
                    show_none=False, no_format=False, preview=False,
                    from_id=""):
	file_id = None
	note_name = note_name.lower()
	note = await db.notes.find_one({'chat_id': int(group_id), 'name': note_name})
	if not note and show_none is True:
		text = get_string("notes", "note_not_found", chat_id)
		all_notes = await db.notes.find({'chat_id': group_id})
		if all_notes.count() > 0:
			check = difflib.get_close_matches(note_name, [d['name'] for d in all_notes])
			if len(check) > 0:
				text += "\nDid you mean `#{}`?".format(check[0])

		await tbot.send_message(chat_id, text, reply_to=msg_id)
		return
	elif not note:
		return None

	if note['file_id']:
		file_id = note['file_id']

	if not file_id:
		file_id = None

	if 'encrypted' not in note or note['encrypted'] is False:
		raw_note_text = note['text']

	elif 'encrypted' in note:
		if note['encrypted'] == 'particle-v1':
			raw_note_text = bz2.decompress(base64.urlsafe_b64decode(note['text'])).decode()

	if no_format is True:
		parse_format = None
		string = raw_note_text
		buttons = ""
	else:
		string, buttons = button_parser(group_id, raw_note_text)
		h = re.search(r"(\[format:(markdown|md|html|none)\])", string)
		if h:
			string = string.replace(h.group(1), "")
			format_raw = h.group(2).lower()
			if format_raw == 'markdown' or format_raw == 'md':
				parse_format = 'md'
			elif format_raw == 'html':
				parse_format = 'html'
			elif format_raw == 'none':
				parse_format = None
		else:
			parse_format = 'md'

		r = re.search(r"(\[preview:(yes|no)\])", string)
		if r:
			string = string.replace(r.group(1), "")
			preview_raw = r.group(2).lower()
			if preview_raw == "yes":
				preview = True
			elif preview_raw == "no":
				preview = False

	if len(string.rstrip()) == 0:
		if no_format is True:
			string = "Note {}\n\n".format(note_name)
		else:
			string = "**Note {}**\n\n".format(note_name)

	if not buttons:
		buttons = None

	if from_id:
		user = await db.user_list.find_one({"user_id": from_id})
		if not user:
			user = await add_user_to_db(await tbot(GetFullUserRequest(from_id)))
		if 'last_name' in user:
			last_name = user['last_name']
			if not last_name:
				last_name = ""
			full_name = user['first_name'] + " " + last_name
		else:
			last_name = None
			full_name = user['first_name']

		if 'username' in user and user['username']:
			username = "@" + user['username']
		else:
			username = None

		chat_name = await db.chat_list.find_one({'chat_id': group_id})
		if chat_name:
			chat_name = chat_name['chat_title']
		else:
			chat_name = "None"

		if no_format is False:
			if parse_format == "md":
				mention_str = await user_link(from_id)
			elif parse_format == "html":
				mention_str = await user_link_html(from_id)
			else:
				mention_str = full_name

			try:
				string = string.format(
					first=user['first_name'],
					last=last_name,
					fullname=full_name,
					username=username,
					id=from_id,
					mention=mention_str,
					chatname=chat_name
				)
			except KeyError as var:
				await tbot.send_message(chat_id, f"variable `{var}` not supported! Please delete it from note.",
				                        reply_to=msg_id)
				return

	try:
		return await tbot.send_message(
			chat_id,
			string,
			buttons=buttons,
			parse_mode=parse_format,
			reply_to=msg_id,
			file=file_id,
			link_preview=preview
		)
	except Exception as err:
		await tbot.send_message(chat_id, str(err))
		logger.error("Error in send_note/send_message: " + str(err))


@decorator.register(cmds='get')
@need_args_dec()
@connection()
async def get_note(message, status, chat_id, chat_title):
	args = message['text'].split(" ", 4)

	note_name = args[1].lower()
	if note_name[0] == "#":
		note_name = note_name[1:]
	if len(args) >= 3 and args[2].lower() == "noformat":
		noformat = True
	elif len(args) >= 3:
		noformat = False
		if len(args) >= 4 and args[3].lower() == "noformat":
			noformat = True
	else:
		noformat = False
	if len(note_name) >= 1:
		await send_note(
			message.chat.id, chat_id, message.message_id, note_name,
			show_none=True, no_format=noformat, from_id=message.from_user.id)


@dp.message_handler(regexp="#(\w+)")
@dp.edited_message_handler(regexp="#(\w+)")
async def check_hashtag(message: types.Message):
	status, chat_id, chat_title = await get_conn_chat(message['from']['id'], message['chat']['id'])
	if status is False:
		await message.reply(chat_id)
		return
	note_name = message['text'][1:].split(" ", 2)[0].lower()
	if len(note_name) >= 1:
		await send_note(
			message['chat']['id'], chat_id, message['message_id'], note_name,
			from_id=message['from']['id'])


@decorator.callback_query_deprecated(b'get_note_')
async def get_note_callback(event):
	data = str(event.data)
	event_data = re.search(r'get_note_(.*)_(.*)', data)
	notename = event_data.group(2)[:-1]
	group_id = event_data.group(1)
	user_id = event.original_update.user_id
	try:
		await send_note(user_id, group_id, None, notename)
		await event.answer(get_string("notes", "pmed_note", event.chat_id))
	except (errors.rpcerrorlist.UserIsBlockedError, errors.rpcerrorlist.PeerIdInvalidError):
		await event.answer(
			get_string("notes", "user_blocked", event.chat_id), alert=True)


@decorator.callback_query_deprecated(b'get_alert_')
async def get_alert_callback(event):
	data = str(event.data)
	event_data = re.search(r'get_alert_(.*)_(.*)', data)
	notename = event_data.group(2)[:-1]
	group_id = event_data.group(1)
	note = await db.notes.find_one({'chat_id': int(group_id), 'name': notename})
	if not note:
		await event.answer(get_string("notes", "cant_find_note", event.chat_id), alert=True)
		return
	text = note['text']
	if len(text) >= 200:
		await event.answer(
			get_string("notes", "note_so_big", event.chat_id), alert=True)
		return

	await event.answer(text, alert=True)


@decorator.callback_query_deprecated(b'get_delete_msg_')
async def del_message_callback(event):
	data = str(event.data)
	event_data = re.search(r'get_delete_msg_(.*)_(.*)', data)
	if 'admin' in event_data.group(2):
		user_id = event.query.user_id
		if await check_group_admin(event, user_id, no_msg=True) is False:
			return
	elif 'user' in event_data.group(2):
		pass
	else:
		await event.answer(
			get_string("notes", "delmsg_no_arg", event.chat_id), alert=True)
		return

	await event.delete()
