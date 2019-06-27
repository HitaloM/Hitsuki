import random
import re
import string

from telethon.tl.custom import Button

from sophie_bot import WHITELISTED, decorator, mongodb
from sophie_bot.modules.bans import ban_user
from sophie_bot.modules.connections import get_conn_chat
from sophie_bot.modules.language import get_string
from sophie_bot.modules.users import (get_chat_admins, get_user,
                                      get_user_and_text, is_user_admin,
                                      user_link)


@decorator.t_command("warn(?!(\w))", arg=True)
async def warn_user(event):
    K = await is_user_admin(event.chat_id, event.from_id)
    if K is False:
        await event.reply(get_string("warns", "user_no_admeme", event.chat_id))
        return
    status, chat_id, chat_title = await get_conn_chat(
        event.from_id, event.chat_id, admin=True, only_in_groups=True)
    if status is False:
        await event.reply(chat_id)
        return

    user, reason = await get_user_and_text(event)
    user_id = int(user['user_id'])
    if user_id in WHITELISTED:
        await event.reply(get_string("warns", "usr_whitelist", event.chat_id))
        return
    if user_id in await get_chat_admins(chat_id):
        await event.reply(get_string("warns", "Admin_no_wrn", event.chat_id))
        return

    rndm = randomString(15)
    mongodb.warns.insert_one({
        'warn_id': rndm,
        'user_id': user_id,
        'group_id': chat_id,
        'reason': str(reason)
    })
    admin_id = event.from_id
    admin = mongodb.user_list.find_one({'user_id': admin_id})
    admin_str = await user_link(admin['user_id'])
    user_str = await user_link(user['user_id'])
    textx = get_string("warns", "warn", event.chat_id)
    text = textx.format(admin=admin_str, user=user_str, chat_name=chat_title)
    if reason:
        textx = get_string("warns", "warn_rsn", event.chat_id)
        text += textx.format(reason=reason)

    old = mongodb.warns.find({
        'user_id': user_id,
        'group_id': chat_id
    })
    h = 0
    for suka in old:
        h += 1

    button = Button.inline("Remove warn", 'remove_warn_{}'.format(rndm))

    warn_limit = mongodb.warnlimit.find_one({'chat_id': chat_id})

    if not warn_limit:
        warn_limit = 3
    else:
        warn_limit = int(warn_limit['num'])

    if h >= warn_limit:
        if await ban_user(event, user_id, chat_id, None) is False:
            return
        textx = get_string("warns", "warn_bun", event.chat_id).format(user=user_str)
        text += textx
        mongodb.warns.delete_many({
            'user_id': user_id,
            'group_id': chat_id
        })
    else:
        textx = get_string("warns", "warn_num", event.chat_id)
        text += textx.format(curr_warns=h, max_warns=warn_limit)

    await event.reply(text, buttons=button, link_preview=False)


@decorator.CallBackQuery(b'remove_warn_')
async def remove_warn(event):
    user_id = event.query.user_id
    K = await is_user_admin(event.chat_id, user_id)
    if K is False:
        await event.answer(get_string("warns", "rmv_warn_admin", event.chat_id))
        return

    warn_id = re.search(r'remove_warn_(.*)', str(event.data)).group(1)[:-1]
    warn = mongodb.warns.find_one({'warn_id': warn_id})
    if warn:
        mongodb.warns.delete_one({'_id': warn['_id']})
    user_str = await user_link(user_id)
    textx = get_string("warns", "rmv_sfl", event.chat_id)
    await event.edit(textx.format(admin=user_str), link_preview=False)


@decorator.t_command("warns", arg=True)
async def user_warns(event):
    status, chat_id, chat_title = await get_conn_chat(
        event.from_id, event.chat_id, admin=True, only_in_groups=True)
    if status is False:
        await event.reply(chat_id)
        return

    user, reason = await get_user_and_text(event)
    if not user:
        return
    user_id = int(user['user_id'])
    if user_id in WHITELISTED:
        await event.reply(
            "There are no warnings for this user!"
        )
        return
    warns = mongodb.warns.find({
        'user_id': user_id,
        'group_id': chat_id
    })
    user_str = await user_link(user_id)
    text = get_string("warns", "warn_list_head", event.chat_id).format(
        user=user_str, chat_name=chat_title)
    H = 0
    for warn in warns:
        H += 1
        rsn = warn['reason']
        if rsn == 'None':
            rsn = "No reason"
        text += "{}: `{}`\n".format(H, rsn)
    if H == 0:
        await event.reply(get_string("warns", "user_hasnt_warned", event.chat_id).format(
            user=user_str, chat_name=chat_title))
        return
    await event.reply(text)


@decorator.t_command("warnlimit", arg=True)
async def warnlimit(event):
    K = await is_user_admin(event.chat_id, event.from_id)
    if K is False:
        await event.reply(get_string("warns", "user_no_admeme", event.chat_id))
        return
    status, chat_id, chat_title = await get_conn_chat(
        event.from_id, event.chat_id, admin=True, only_in_groups=True)
    if status is False:
        await event.reply(chat_id)
        return
    arg = event.pattern_match.group(2)
    old = mongodb.warnlimit.find_one({'chat_id': chat_id})
    if not arg:
        if old:
            num = old['num']
        else:
            num = 3
        await event.reply(get_string("warns", "warn_limit", event.chat_id).format(
            chat_name=chat_title, num=num))
    else:
        if old:
            mongodb.warnlimit.delete_one({'_id': old['_id']})
        num = int(arg)
        mongodb.warnlimit.insert_one({
            'chat_id': chat_id,
            'num': num
        })
        await event.reply(get_string("warns", "warn_limit_upd", event.chat_id).format(num))


@decorator.t_command("resetwarns", arg=True)
async def resetwarns(event):
    K = await is_user_admin(event.chat_id, event.from_id)
    if K is False:
        await event.reply(get_string("warns", "user_no_admeme", event.chat_id))
        return
    status, chat_id, chat_title = await get_conn_chat(
        event.from_id, event.chat_id, admin=True, only_in_groups=True)
    if status is False:
        await event.reply(chat_id)
        return

    user = await get_user(event)
    user_id = int(user['user_id'])
    admin = event.from_id
    admin_str = await user_link(admin)
    user_str = await user_link(user_id)
    chack = mongodb.warns.find({'group_id': chat_id, 'user_id': user_id})

    if chack:
        mongodb.warns.delete_many({'group_id': chat_id, 'user_id': user_id})
        text = get_string("warns", "purged_warns", event.chat_id)
        await event.reply(text.format(admin=admin_str, user=user_str))
    else:
        text = get_string("warns", "usr_no_wrn", event.chat_id)
        await event.reply(text.format(user=user_str))


def randomString(stringLength):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for i in range(stringLength))
