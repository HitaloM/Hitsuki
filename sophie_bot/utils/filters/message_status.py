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
from aiogram.dispatcher.filters import BoundFilter

from sophie_bot import dp


class NotForwarded(BoundFilter):
	key = 'not_forwarded'

	def __init__(self, not_forwarded):
		self.not_forwarded = not_forwarded

	async def check(self, message: types.Message):
		if 'forward_from' not in message:
			return True


class NoArgs(BoundFilter):
	key = 'no_args'

	def __init__(self, no_args):
		self.no_args = no_args

	async def check(self, message: types.Message):
		if not len(message.text.split(' ')) > 1:
			return True


class HasArgs(BoundFilter):
	key = 'has_args'

	def __init__(self, has_args):
		self.has_args = has_args

	async def check(self, message: types.Message):
		if len(message.text.split(' ')) > 1:
			return True


dp.filters_factory.bind(NotForwarded)
dp.filters_factory.bind(NoArgs)
dp.filters_factory.bind(HasArgs)
