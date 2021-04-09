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

import re

from telethon import events
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import MessageEntityMentionName

from hitsuki.decorator import register
from hitsuki.services.mongo import db
from hitsuki.services.telethon import tbot
from .utils.disable import disableable_dec
from .utils.message import get_arg


def insurgent():
    def decorator(func):
        tbot.add_event_handler(func, events.NewMessage(incoming=True))
        tbot.add_event_handler(func, events.MessageEdited(incoming=True))

    return decorator


async def user_link(user_id):
    user = await db.user_list.find_one({"user_id": user_id})
    user_name = None

    if user:
        try:
            user_name = user["first_name"]
        except (ValueError, TypeError):
            user_name = str(user_id)

    return '<a href="tg://user?id={id}">{name}</a>'.format(name=user_name, id=user_id)


@register(cmds="afk")
@disableable_dec("afk")
async def afk(event):
    arg = get_arg(event)
    if not arg:
        reason = "No reason"
    else:
        reason = get_arg(event)
    user_afk = await db.afk.find_one({"user": event.from_user.id})
    if user_afk:
        return
    await db.afk.insert_one({"user": event.from_user.id, "reason": reason})
    text = "{} is AFK!".format(await user_link(event.from_user.id))
    if reason:
        text += "\nReason: " + reason
    await event.reply(text)


async def get_user(event):
    if event.reply_to_msg_id:
        previous_message = await event.get_reply_message()
        replied_user = await event.client(
            GetFullUserRequest(previous_message.sender_id)
        )
    else:
        user = re.search("@(\w*)", event.text)
        if not user:
            return
        user = user.group(0)

        if user.isnumeric():
            user = int(user)

        if not user:
            self_user = await event.client.get_me()
            user = self_user.id

        if event.message.entities is not None:
            probable_user_mention_entity = event.message.entities[0]

            if isinstance(probable_user_mention_entity, MessageEntityMentionName):
                user_id = probable_user_mention_entity.user_id
                replied_user = await event.client(GetFullUserRequest(user_id))
                return replied_user
        try:
            user_object = await event.client.get_entity(user)
            replied_user = await event.client(GetFullUserRequest(user_object.id))
        except (TypeError, ValueError):
            return None

    return replied_user


@insurgent()
async def check_afk(event):
    user_afk = await db.afk.find_one({"user": event.sender_id})
    if user_afk:
        afk_cmd = re.findall("[!/]afk(.*)", event.text)
        if not afk_cmd:
            await event.reply(
                "{} is not AFK anymore!".format(await user_link(event.sender_id)),
                parse_mode="html",
            )
            await db.afk.delete_one({"_id": user_afk["_id"]})

    user = await get_user(event)
    if not user:
        return
    user_afk = await db.afk.find_one({"user": user.user.id})
    if user_afk:
        await event.reply(
            "{} is AFK!\nReason: {}".format(
                await user_link(user.user.id), user_afk["reason"]
            ),
            parse_mode="html",
        )
