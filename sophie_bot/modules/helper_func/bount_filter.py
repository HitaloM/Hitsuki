from sophie_bot import OWNER_ID, bot, dp, mongodb

from aiogram.dispatcher.filters import BoundFilter
from aiogram import types


class IsAdmin(BoundFilter):
    key = 'is_admin'

    def __init__(self, is_admin):
        self.is_admin = is_admin

    async def check(self, message: types.Message):
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        return member.is_admin()


class IsOwner(BoundFilter):
    key = 'is_owner'

    def __init__(self, is_owner):
        self.is_owner = is_owner

    async def check(self, message: types.Message):
        if message.from_user.id == OWNER_ID:
            return True


class NotGbanned(BoundFilter):
    key = 'not_gbanned'

    def __init__(self, not_gbanned):
        self.not_gbanned = not_gbanned

    async def check(self, message: types.Message):
        check = mongodb.blacklisted_users.find_one({'user': message.from_user.id})
        if not check:
            return True


class NotForwarded(BoundFilter):
    key = 'not_forwarded'

    def __init__(self, not_forwarded):
        self.not_forwarded = not_forwarded

    async def check(self, message: types.Message):
        if 'forward_from' not in message:
            return True


class Only_PM(BoundFilter):
    key = 'only_pm'

    def __init__(self, only_pm):
        self.only_pm = only_pm

    async def check(self, message: types.Message):
        if message.from_user.id == message.chat.id:
            return True


class Only_In_Groups(BoundFilter):
    key = 'only_groups'

    def __init__(self, only_groups):
        self.only_groups = only_groups

    async def check(self, message: types.Message):
        if not message.from_user.id == message.chat.id:
            return True


dp.filters_factory.bind(IsAdmin)
dp.filters_factory.bind(IsOwner)
dp.filters_factory.bind(NotGbanned)
dp.filters_factory.bind(NotForwarded)
dp.filters_factory.bind(Only_PM)
dp.filters_factory.bind(Only_In_Groups)
