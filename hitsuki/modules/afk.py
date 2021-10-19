# Copyright (C) 2018 - 2020 MrYacha. All rights reserved. Source code available under the AGPL.
# Copyright (C) 2021 HitaloSama.
# Copyright (C) 2019 Aiogram.
#
# This file is part of Hitsuki (Telegram Bot)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import html
import re

from aiogram.utils.exceptions import BadRequest, ChatAdminRequired
from telethon.errors import UserIdInvalidError
from telethon.errors.rpcerrorlist import UsernameInvalidError

from hitsuki.decorator import register
from hitsuki.services.mongo import db

from .utils.disable import disableable_dec
from .utils.language import get_strings_dec
from .utils.message import get_args_str
from .utils.user_details import get_user, get_user_by_id, get_user_link


@register(cmds="afk")
@disableable_dec("afk")
@get_strings_dec("afk")
async def afk(message, strings):
    arg = get_args_str(message)

    # dont support AFK as anon admin
    if message.from_user.id in (1087968824, 777000):
        await message.reply(strings["afk_anon"])
        return

    if len(arg) > 100:
        arg = arg[:100]

    reason = "No reason" if not arg else arg
    user = await get_user_by_id(message.from_user.id)

    user_afk = await db.afk.find_one({"user": user["user_id"]})
    if user_afk:
        return

    await db.afk.insert_one({"user": user["user_id"], "reason": reason})
    text = strings["is_afk"].format(
        user=(await get_user_link(user["user_id"])), reason=html.escape(reason)
    )
    sent = await message.reply(text)
    await asyncio.sleep(6)
    try:
        await message.delete()
        await sent.delete()
    except (BadRequest, ChatAdminRequired):
        return


@register(f="text", allow_edited=False)
@get_strings_dec("afk")
async def check_afk(message, strings):
    if bool(message.reply_to_message) and message.reply_to_message.from_user.id in (
        1087968824,
        777000,
    ):
        return
    if message.from_user.id in (1087968824, 777000):
        return
    user_afk = await db.afk.find_one({"user": message.from_user.id})
    if user_afk:
        afk_cmd = re.findall("^[!/]afk(.*)", message.text)
        if not afk_cmd:
            sent = await message.reply(
                strings["unafk"].format(
                    user=(await get_user_link(message.from_user.id))
                )
            )
            await db.afk.delete_one({"_id": user_afk["_id"]})
            await asyncio.sleep(6)
            try:
                await sent.delete()
            except (BadRequest, ChatAdminRequired):
                return

    try:
        user = await get_user(message)
    except (UserIdInvalidError, ValueError, UsernameInvalidError):
        return

    if not user:
        return

    user_afk = await db.afk.find_one({"user": user["user_id"]})

    if user_afk:
        sent = await message.reply(
            strings["is_afk"].format(
                user=(await get_user_link(user["user_id"])),
                reason=html.escape(user_afk["reason"]),
            )
        )
        await asyncio.sleep(6)
        try:
            await sent.delete()
        except (BadRequest, ChatAdminRequired):
            return
