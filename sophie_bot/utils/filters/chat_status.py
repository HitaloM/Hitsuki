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


class OnlyPM(BoundFilter):
    key = 'only_pm'

    def __init__(self, only_pm):
        self.only_pm = only_pm

    async def check(self, message: types.Message):
        if message.from_user.id == message.chat.id:
            return True


class OnlyGroups(BoundFilter):
    key = 'only_groups'

    def __init__(self, only_groups):
        self.only_groups = only_groups

    async def check(self, message: types.Message):
        if not message.from_user.id == message.chat.id:
            return True


dp.filters_factory.bind(OnlyPM)
dp.filters_factory.bind(OnlyGroups)
