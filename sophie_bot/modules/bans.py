import time

from sophie_bot import WHITELISTED, bot
from sophie_bot import decorator
from sophie_bot.modules.connections import get_conn_chat
from sophie_bot.modules.language import get_string
from sophie_bot.modules.users import (get_user, get_user_and_text,
                                      is_user_admin, user_link)

from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights


@decorator.command("ban", arg=True)
async def ban(event):
    K = await is_user_admin(event.chat_id, event.from_id)
    if K is False:
        await event.reply(get_string("bans", "u_dont_have_rights",
                          event.chat_id))
        return
    status, chat_id, chat_title = await get_conn_chat(
        event.from_id, event.chat_id, admin=True, only_in_groups=True)
    if status is False:
        await event.reply(chat_id)
        return
    user, reason = await get_user_and_text(event)
    if await ban_user(event, user['user_id'], chat_id, None) is True:
        admin_str = await user_link(event.from_id)
        user_str = await user_link(user['user_id'])
        text = get_string("bans", "user_banned", event.chat_id)
        text += get_string("bans", "reason", event.chat_id)
        await event.reply(text.format(
            user=user_str, admin=admin_str, chat_name=chat_title, reason=reason),
            link_preview=False
        )


@decorator.command("tban", arg=True)
async def tban(event):
    K = await is_user_admin(event.chat_id, event.from_id)
    if K is False:
        await event.reply(get_string("bans", "u_dont_have_rights",
                          event.chat_id))
        return
    status, chat_id, chat_title = await get_conn_chat(
        event.from_id, event.chat_id, admin=True, only_in_groups=True)
    if status is False:
        await event.reply(chat_id)
        return
    user, data = await get_user_and_text(event)
    data = data.split(' ', 2)
    reason = data[1]
    time_val = data[0]

    unit = time_val[-1]
    if any(time_val.endswith(unit) for unit in ('m', 'h', 'd')):
        time_num = time_val[:-1]  # type: str
        if unit == 'm':
            bantime = int(time.time() + int(time_num) * 60)
            unit_str = 'minutes'
        elif unit == 'h':
            bantime = int(time.time() + int(time_num) * 60 * 60)
            unit_str = 'hours'
        elif unit == 'd':
            bantime = int(time.time() + int(time_num) * 24 * 60 * 60)
            unit_str = 'days'
        else:
            await event.reply(get_string("bans", "time_var_incorrect",
                              event.chat_id))

    if await ban_user(event, user.id, chat_id, bantime) is True:
        admin_str = await user_link(event.from_id)
        user_str = await user_link(user['user_id'])
        text = "User {} banned by {} in {}!\n".format(user_str, admin_str, chat_title)
        text += "For `{}` {}\n".format(time_val[:-1], unit_str)
        text += "Reason: `{}`".format(reason)
        await event.reply(text, link_preview=False)


@decorator.command("kick", arg=True)
async def kick(event):
    K = await is_user_admin(event.chat_id, event.from_id)
    if K is False:
        await event.reply(get_string("bans", "u_dont_have_rights_kick",
                          event.chat_id))
        return
    status, chat_id, chat_title = await get_conn_chat(
        event.from_id, event.chat_id, admin=True, only_in_groups=True)
    if status is False:
        await event.reply(chat_id)
        return
    user = await get_user(event)
    if await kick_user(event, user['user_id'], chat_id) is True:
        admin_str = await user_link(event.from_id)
        user_str = await user_link(user['user_id'])
        text = get_string("bans", "user_kicked", event.chat_id)
        await event.reply(text.format(admin=admin_str, user=user_str, chat_name=chat_title))


@decorator.command("unban", arg=True)
async def unban(event):
    K = await is_user_admin(event.chat_id, event.from_id)
    if K is False:
        await event.reply(get_string("bans", "u_dont_have_rights_unban",
                          event.chat_id))
        return
    status, chat_id, chat_title = await get_conn_chat(
        event.from_id, event.chat_id, admin=True, only_in_groups=True)
    if status is False:
        await event.reply(chat_id)
        return
    user, data = await get_user_and_text(event)
    if await unban_user(event, user['user_id'], chat_id):
        admin_str = await user_link(event.from_id)
        user_str = await user_link(user['user_id'])
        text = get_string("bans", "user_unbanned", event.chat_id)
        await event.reply(text.format(admin=admin_str, user=user_str, chat_name=chat_title))


@decorator.command("mute", arg=True)
async def muter(event):
    K = await is_user_admin(event.chat_id, event.from_id)
    if K is False:
        await event.reply(get_string("bans", "u_dont_have_rights_mute",
                          event.chat_id))
        return
    status, chat_id, chat_title = await get_conn_chat(
        event.from_id, event.chat_id, admin=True, only_in_groups=True)
    if status is False:
        await event.reply(chat_id)
        return
    user, data = await get_user_and_text(event)
    if await mute_user(event, user['user_id'], chat_id):
        admin_str = await user_link(event.from_id)
        user_str = await user_link(user['user_id'])
        text = get_string("bans", "user_mooted", event.chat_id)
        await event.reply(text.format(admin=admin_str, user=user_str, chat_name=chat_title))


@decorator.command("unmute", arg=True)
async def unmoot(event):
    K = await is_user_admin(event.chat_id, event.from_id)
    if K is False:
        await event.reply(get_string("bans", "u_dont_have_rights_unmute", event.chat_id))
        return
    status, chat_id, chat_title = await get_conn_chat(
        event.from_id, event.chat_id, admin=True, only_in_groups=True)
    if status is False:
        await event.reply(chat_id)
        return
    user = get_user(event)
    if await unmute_user(event, user['user_id'], chat_id):
        admin_str = await user_link(event.from_id)
        user_str = await user_link(user['user_id'])
        text = get_string("bans", "user_unmooted", event.chat_id)
        await event.reply(text.format(admin=admin_str, user=user_str, chat_name=chat_title))


async def ban_user(event, user_id, chat_id, time_val):
    K = await is_user_admin(event.chat_id, event.from_id)
    if K is False:
        await event.reply(get_string("bans", "u_dont_have_rights",
                          event.chat_id))
        return

    banned_rights = ChatBannedRights(
        until_date=time_val,
        view_messages=True,
        send_messages=True,
        send_media=True,
        send_stickers=True,
        send_gifs=True,
        send_games=True,
        send_inline=True,
        embed_links=True,
    )

    bot_id = await bot.get_me()
    bot_id = bot_id.id

    if str(user_id) in WHITELISTED:
        await event.reply("This user is whitelisted")
        return

    if user_id == bot_id:
        await event.reply(get_string("bans", "bot_cant_be_banned",
                          event.chat_id))
        return False
    if await is_user_admin(chat_id, user_id) is True:
        await event.reply(get_string("bans", "user_admin_ban",
                          event.chat_id))
        return False

    try:
        await event.client(
            EditBannedRequest(
                chat_id,
                user_id,
                banned_rights
            )
        )

    except Exception as err:
        await event.edit(str(err))
        return False

    return True


async def kick_user(event, user_id, chat_id):
    K = await is_user_admin(event.chat_id, event.from_id)
    if K is False:
        await event.reply(get_string("bans", "u_dont_have_rights_kick",
                          event.chat_id))
        return
    banned_rights = ChatBannedRights(
        until_date=None,
        send_messages=True,
        view_messages=True
    )

    unbanned_rights = ChatBannedRights(
        until_date=None,
        view_messages=False,
        send_messages=False
    )

    bot_id = await bot.get_me()
    bot_id = bot_id.id

    if user_id == bot_id:
        await event.reply(get_string("bans", "bot_cant_be_kicked",
                          event.chat_id))
        return False
    if await is_user_admin(chat_id, user_id) is True:
        await event.reply(get_string("bans", "user_admin_kick", event.chat_id))
        return False

    try:
        await event.client(
            EditBannedRequest(
                chat_id,
                user_id,
                banned_rights
            )
        )

        await event.client(
            EditBannedRequest(
                chat_id,
                user_id,
                unbanned_rights
            )
        )

    except Exception as err:
        print(str(err))
        return False
    return True


async def unban_user(event, user_id, chat_id):
    K = await is_user_admin(event.chat_id, event.from_id)
    if K is False:
        await event.reply(get_string(
            "bans", "u_dont_have_rights_unban", event.chat_id))
        return

    unbanned_rights = ChatBannedRights(
        until_date=None,
        view_messages=False,
        send_messages=False,
        send_media=False,
        send_stickers=False,
        send_gifs=False,
        send_games=False,
        send_inline=False,
        embed_links=False,
    )

    bot_id = await bot.get_me()
    bot_id = bot_id.id

    if user_id == bot_id:
        await event.reply(get_string("bans", "bot_cant_be_unbanned",
                          event.chat_id))
        return False
    if await is_user_admin(chat_id, user_id) is True:
        await event.reply(get_string("bans", "user_admin_unban",
                          event.chat_id))
        return False
    try:
        await event.client(
            EditBannedRequest(
                chat_id,
                user_id,
                unbanned_rights
            )
        )
    except Exception as err:
        print(str(err))
        return False
    return True


async def mute_user(event, user_id, chat_id):
    K = await is_user_admin(event.chat_id, event.from_id)
    if K is False:
        await event.reply(get_string("bans", "u_dont_have_rights",
                          event.chat_id))
        return
    muted_rights = ChatBannedRights(
        until_date=None,
        send_messages=True
    )

    bot_id = await bot.get_me()
    bot_id = bot_id.id

    if user_id == bot_id:
        await event.reply(get_string("bans", "bot_cant_be_muted",
                          event.chat_id))
        return False
    if await is_user_admin(chat_id, user_id) is None:
        await event.reply(get_string("bans", "user_admin_mute", event.chat_id))
        return False
    try:
        await event.client(
            EditBannedRequest(
                chat_id,
                user_id,
                muted_rights
            )
        )

    except Exception as err:
        print(str(err))
        return False
    return True


async def unmute_user(event, user_id, chat_id):
    K = await is_user_admin(event.chat_id, event.from_id)
    if K is False:
        await event.reply(get_string("bans", "u_dont_have_rights_unmute", event.chat_id))
        return
    muted_rights = ChatBannedRights(
        until_date=None,
        send_messages=False
    )

    bot_id = await bot.get_me()
    bot_id = bot_id.id

    if user_id == bot_id:
        await event.reply(get_string("bans", "bot_cant_be_unmuted", event.chat_id))
        return False
    if await is_user_admin(chat_id, user_id) is None:
        await event.reply(get_string("bans", "user_admin_unmute", event.chat_id))
        return False
    try:
        await event.client(
            EditBannedRequest(
                chat_id,
                user_id,
                muted_rights
            )
        )

    except Exception as err:
        print(str(err))
        return False
    return True
