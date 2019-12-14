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

from sophie_bot import OPERATORS, dp
from sophie_bot.config import get_int_key
from sophie_bot.modules.utils.language import get_strings_dec
from sophie_bot.modules.utils.user_details import is_user_admin
from sophie_bot.services.mongo import mongodb


class IsAdmin(BoundFilter):
    key = 'is_admin'

    def __init__(self, is_admin):
        self.is_admin = is_admin

    @get_strings_dec('global')
    async def check(self, message: types.Message, strings):
        if not await is_user_admin(message.chat.id, message.from_user.id):
            await message.reply(strings['u_not_admin'])
            return False
        return True


class IsOwner(BoundFilter):
    key = 'is_owner'

    def __init__(self, is_owner):
        self.is_owner = is_owner

    async def check(self, message: types.Message):
        if message.from_user.id == get_int_key("OWNER_ID"):
            return True


class IsOP(BoundFilter):
    key = 'is_op'

    def __init__(self, is_op):
        self.is_owner = is_op

    async def check(self, message: types.Message):
        if message.from_user.id in OPERATORS:
            return True


class NotGbanned(BoundFilter):
    key = 'not_gbanned'

    def __init__(self, not_gbanned):
        self.not_gbanned = not_gbanned

    async def check(self, message: types.Message):
        check = mongodb.blacklisted_users.find_one({'user': message.from_user.id})
        if not check:
            return True


dp.filters_factory.bind(IsAdmin)
dp.filters_factory.bind(IsOwner)
dp.filters_factory.bind(NotGbanned)
dp.filters_factory.bind(IsOP)
