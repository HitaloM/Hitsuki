# Copyright (C) 2019 The Raphielscape Company LLC.
# Copyright (C) 2018-2019 MrYacha
# Copyright (C) 2017-2019 Aiogram
#
# This file is part of SophieBot.
#
# SophieBot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.

from datetime import timedelta


# elif raw_button[1] == 'note':
# t = InlineKeyboardButton(raw_button[0], callback_data='get_note_{}_{}'.format(chat_id, raw_button[2]))
# elif raw_button[1] == 'alert':
# t = InlineKeyboardButton(raw_button[0], callback_data='get_alert_{}_{}'.format(chat_id, raw_button[2]))
# elif raw_button[1] == 'deletemsg':
# t = InlineKeyboardButton(raw_button[0], callback_data='get_delete_msg_{}_{}'.format(chat_id, raw_button[2]))


class InvalidTimeUnit(Exception):
	pass


def get_arg(message):
	return message.get_args().split(' ')[0]


def get_args(message):
	return message.get_args().split(' ')


def get_cmd(message):
	cmd = message.get_command().lower()[1:].split('@')[0]
	return cmd


def convert_time(time_val):
	if not any(time_val.endswith(unit) for unit in ('m', 'h', 'd')):
		raise TypeError

	time_num = int(time_val[:-1])
	unit = time_val[-1]
	kwargs = {}

	if unit == 'm':
		kwargs['minutes'] = time_num
		unit_str = 'minutes'
	elif unit == 'h':
		kwargs['hours'] = time_num
		unit_str = 'hours'
	elif unit == 'd':
		kwargs['days'] = time_num
		unit_str = 'days'
	else:
		raise InvalidTimeUnit()

	val = timedelta(**kwargs)

	return val


def need_args_dec(num=1):
	def wrapped(func):
		async def wrapped_1(*args, **kwargs):
			message = args[0]
			if len(message.text.split(" ")) > num:
				return await func(*args, **kwargs)
			else:
				await message.reply("No enoff args!")

		return wrapped_1

	return wrapped
