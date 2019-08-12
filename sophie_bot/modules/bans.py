import time

from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import ChannelParticipantBanned

from sophie_bot import BOT_ID, WHITELISTED, tbot, decorator, mongodb, bot
from sophie_bot.modules.connections import connection
from sophie_bot.modules.language import get_string, get_strings_dec
from sophie_bot.modules.users import (is_user_admin, user_admin_dec,
                                      aio_get_user, user_link_html)


@decorator.command("ban")
@user_admin_dec
@connection(admin=True, only_in_groups=True)
@get_strings_dec('bans')
async def ban(message, strings, status, chat_id, chat_title):
    user, reason = await aio_get_user(message)
    if not user:
        return
    if await ban_user(message, user['user_id'], chat_id, None) is True:
        admin_str = await user_link_html(message.from_user.id)
        user_str = await user_link_html(user['user_id'])
        text = strings["user_banned"]
        if reason:
            text += strings["reason"].format(reason=reason)
        await message.reply(text.format(
            user=user_str, admin=admin_str, chat_name=chat_title),
            disable_web_page_preview=True
        )


@decorator.command("tban")
@user_admin_dec
@connection(admin=True, only_in_groups=True)
async def tban(message, status, chat_id, chat_title):
    user, data = await aio_get_user(message)
    if not user:
        return
    data = data.split(' ', 2)

    if len(data) > 1:
        reason = data[1]
    else:
        reason = None

    time_val = data[0]

    if any(time_val.endswith(unit) for unit in ('m', 'h', 'd')):
        bantime, unit_str = await convert_time(message, time_val)

    if await ban_user(message, user['user_id'], chat_id, bantime) is True:
        admin_str = await user_link_html(message.from_user.id)
        user_str = await user_link_html(user['user_id'])
        text = "User {} banned by {} in {}!\n".format(user_str, admin_str, chat_title)
        text += "For <code>{}</code> {}\n".format(time_val[:-1], unit_str)
        if reason:
            text += "Reason: <code>{}</code>".format(reason)
        await message.reply(text, disable_web_page_preview=True)


@decorator.command("kick")
@user_admin_dec
@connection(admin=True, only_in_groups=True)
@get_strings_dec('bans')
async def kick(message, strings, status, chat_id, chat_title):
    user, text = await aio_get_user(message)
    if not user:
        return
    if await kick_user(message, user['user_id'], chat_id) is True:
        admin_str = await user_link_html(message.from_user.id)
        user_str = await user_link_html(user['user_id'])
        text = strings["user_kicked"]
        await message.reply(text.format(admin=admin_str, user=user_str, chat_name=chat_title))


@decorator.command("unban")
@user_admin_dec
@connection(admin=True, only_in_groups=True)
@get_strings_dec("bans")
async def unban(message, strings, status, chat_id, chat_title):
    user, text = await aio_get_user(message)
    if not user:
        return
    if await unban_user(message, user['user_id'], chat_id):
        admin_str = await user_link_html(message.from_user.id)
        user_str = await user_link_html(user['user_id'])
        text = strings["user_unbanned"]

        gbanned = mongodb.blacklisted_users.find_one({'user': user['user_id']})
        if gbanned:
            text += strings["user_gbanned"].format(
                reason=gbanned['reason']
            )

        await message.reply(text.format(admin=admin_str, user=user_str, chat_name=chat_title))


@decorator.command("mute")
@user_admin_dec
@connection(admin=True, only_in_groups=True)
@get_strings_dec("bans")
async def muter(message, strings, status, chat_id, chat_title):
    user, text = await aio_get_user(message)
    if not user:
        return
    if await mute_user(message, user['user_id'], chat_id, None):
        admin_str = await user_link_html(message.from_user.id)
        user_str = await user_link_html(user['user_id'])
        text = strings["user_mooted"]
        await message.reply(text.format(admin=admin_str, user=user_str, chat_name=chat_title))


@decorator.command("unmute")
@user_admin_dec
@connection(admin=True, only_in_groups=True)
@get_strings_dec("bans")
async def unmute(message, strings, status, chat_id, chat_title):
    user, text = await aio_get_user(message)
    if not user:
        return
    if await unmute_user(message, user['user_id'], chat_id):
        admin_str = await user_link_html(message.from_user.id)
        user_str = await user_link_html(user['user_id'])
        text = strings["user_unmooted"]
        await message.reply(text.format(admin=admin_str, user=user_str, chat_name=chat_title))


@decorator.command("kickme")
@get_strings_dec("bans")
async def kickme(message, strings):
    user = message.from_user.id
    chat = message.chat.id

    if await ban_user(message, user, chat, None) is True:
        await message.reply(strings["kickme_success"])


@decorator.command("tmute")
@user_admin_dec
@connection(admin=True, only_in_groups=True)
@get_strings_dec("bans")
async def tmute(message, strings, status, chat_id, chat_title):
    user, data = await aio_get_user(message)
    if not user:
        return
    data = data.split(' ', 2)
    time_val = data[0]

    if any(time_val.endswith(unit) for unit in ('m', 'h', 'd')):
        mutetime, unit_str = await convert_time(message, time_val)

        if await mute_user(message, user['user_id'], chat_id, mutetime) is True:
            admin_str = await user_link_html(message.from_user.id)
            user_str = await user_link_html(user['user_id'])
            await message.reply(strings["tmute_sucess"].format(
                admin=admin_str, user=user_str,
                time=time_val[:-1], unit=unit_str))


async def ban_user(message, user_id, chat_id, time_val, no_msg=False):
    real_chat_id = message.chat.id

    if str(user_id) in WHITELISTED:
        if no_msg is False:
            await message.reply("This user is whitelisted")
        return

    if user_id == BOT_ID:
        if no_msg is False:
            await message.reply(get_string("bans", "bot_cant_be_banned", real_chat_id))
        return False
    if await is_user_admin(chat_id, user_id) is True:
        if no_msg is False:
            await message.reply(get_string("bans", "user_admin_ban", real_chat_id))
        return False

    await bot.kick_chat_member(chat_id, user_id)

    return True


async def kick_user(message, user_id, chat_id, no_msg=False):
    real_chat_id = message.chat.id

    if user_id == BOT_ID:
        if no_msg is False:
            await message.reply(get_string("bans", "bot_cant_be_kicked", real_chat_id))
        return False
    if await is_user_admin(chat_id, user_id) is True:
        if no_msg is False:
            await message.reply(get_string("bans", "user_admin_kick", real_chat_id))
        return False

    await bot.kick_chat_member(chat_id, user_id)
    await bot.unban_chat_member(chat_id, user_id)

    return True


async def unban_user(message, user_id, chat_id):
    real_chat_id = message.chat.id

    if user_id == BOT_ID:
        await message.reply(get_string("bans", "bot_cant_be_unbanned", real_chat_id))
        return False
    try:
        peep = await tbot(GetParticipantRequest(chat_id, user_id))

        if not isinstance(peep.participant, ChannelParticipantBanned):
            await message.reply(get_string('bans', 'usernt_banned', real_chat_id))
            return False
    except Exception:
        pass

    await bot.unban_chat_member(chat_id, user_id)
    return True


async def mute_user(message, user_id, chat_id, time_val):
    real_chat_id = message.chat.id
    if str(user_id) in WHITELISTED:
        await message.reply("This user is whitelisted")
        return

    if user_id == BOT_ID:
        await message.reply(get_string("bans", "bot_cant_be_muted", real_chat_id))
        return False
    if await is_user_admin(chat_id, user_id) is None:
        await message.reply(get_string("bans", "user_admin_mute", real_chat_id))
        return False

    await bot.restrict_chat_member(
        chat_id,
        user_id,
        time_val,
        can_send_messages=False
    )

    return True


async def unmute_user(message, user_id, chat_id):
    real_chat_id = message.chat.id

    if user_id == BOT_ID:
        await message.reply(get_string("bans", "bot_cant_be_unmuted", real_chat_id))
        return False
    if await is_user_admin(chat_id, user_id) is None:
        await message.reply(get_string("bans", "user_admin_unmute", real_chat_id))
        return False

    await bot.restrict_chat_member(
        chat_id,
        user_id,
        can_send_messages=True
    )

    return True


async def convert_time(event, time_val):

    if hasattr(event, 'chat_id'):
        chat_id = event.chat_id
    elif hasattr(event, 'chat'):
        chat_id = event.chat.id

    if any(time_val.endswith(unit) for unit in ('m', 'h', 'd')):
        time_num = time_val[:-1]
        unit = time_val[-1]
        if unit == 'm':
            mutetime = int(time.time() + int(time_num) * 60)
            unit_str = 'minutes'
        elif unit == 'h':
            mutetime = int(time.time() + int(time_num) * 60 * 60)
            unit_str = 'hours'
        elif unit == 'd':
            mutetime = int(time.time() + int(time_num) * 24 * 60 * 60)
            unit_str = 'days'
        else:
            return await event.reply(get_string("bans", "time_var_incorrect", chat_id))

        return mutetime, unit_str
