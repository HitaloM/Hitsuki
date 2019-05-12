import random
import re
import string

from sophie_bot import BOT_NICK, WHITELISTED, bot, mongodb
from sophie_bot.events import register
from sophie_bot.modules.bans import ban_user
from sophie_bot.modules.users import get_chat_admins, get_user_and_text, is_user_admin, user_link

from telethon import events
from telethon.tl.custom import Button


@register(incoming=True, pattern="^[!/]warn(?!(\w)) ?(@{})?(.*)".format(BOT_NICK))
async def warn_user(event):
    K = await is_user_admin(event.chat_id, event.from_id)
    if K is False:
        await event.reply("You're not an admin!")
        return

    user, reason = await get_user_and_text(event)
    user_id = int(user['user_id'])
    chat_id = event.chat_id
    if user_id in WHITELISTED:
        await event.reply("This is one of the whitelisted user!")
        return
    if user_id in await get_chat_admins(chat_id):
        await event.reply("Heck, I can't warn the admins!")
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
    text = "{} have warned {}\n".format(admin_str, user_str)
    if reason:
        text += "Reason: `{}`\n".format(reason)

    old = mongodb.warns.find({
        'user_id': user_id,
        'group_id': chat_id
    })
    h = 0
    for suka in old:
        h += 1

    button = Button.inline("Remove warn", 'remove_warn_{}'.format(rndm))

    warn_limit = mongodb.warnlimit.find_one({'chat_id': event.chat_id})

    if not warn_limit:
        warn_limit = 3
    else:
        warn_limit = int(warn_limit['num'])

    if h >= warn_limit:
        if await ban_user(event, user_id, chat_id, None) is False:
            return
        text += "Warnings has been exceeded! {} has been banned!".format(user_str)
        mongodb.warns.delete_many({
            'user_id': user_id,
            'group_id': chat_id
        })
    else:
        text += "Warns: {}/{}\n".format(h, warn_limit)

    await event.reply(text, buttons=button, link_preview=False)


@bot.on(events.CallbackQuery(data=re.compile(b'remove_warn_')))
async def remove_warn(event):
    user_id = event.query.user_id
    K = await is_user_admin(event.chat_id, user_id)
    if K is False:
        await event.answer("You're not an admin, Only admins can do!")
        return

    warn_id = re.search(r'remove_warn_(.*)', str(event.data)).group(1)[:-1]
    warn = mongodb.warns.find_one({'warn_id': warn_id})
    if warn:
        mongodb.notes.delete_one({'_id': warn['_id']})
    user_str = await user_link(user_id)
    await event.edit("Warn removed by {}".format(user_str), link_preview=False)


@register(incoming=True, pattern="^[!/]warns ?(@{})?(.*)".format(BOT_NICK))
async def user_warns(event):
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
        'group_id': event.chat_id
    })
    user_str = await user_link(user_id)
    chat_title = mongodb.chat_list.find_one({
        'chat_id': event.chat_id})['chat_title']
    text = "{}'s **warnings:**\n".format(user_str)
    H = 0
    for warn in warns:
        H += 1
        rsn = warn['reason']
        if rsn == 'None':
            rsn = "No reason"
        text += "{}: `{}`\n".format(H, rsn)
    if H == 0:
        await event.reply("{} hasn't been warned in **{}** before!".format(
            user_str, chat_title))
        return
    await event.reply(text)


@register(incoming=True, pattern="^[!/]warnlimit ?(@{})?(.*)".format(BOT_NICK))
async def warnlimit(event):
    arg = event.pattern_match.group(2)
    old = mongodb.warnlimit.find_one({'chat_id': event.chat_id})
    if not arg:
        if old:
            num = old['num']
        else:
            num = 3
        await event.reply("Warn limit is currently: `{}`".format(num))
    else:
        if old:
            mongodb.warnlimit.delete_one({'_id': old['_id']})
        num = int(arg)
        mongodb.warnlimit.insert_one({
            'chat_id': event.chat_id,
            'num': num
        })
        await event.reply("Warn limit has been updated to {}!".format(num))


def randomString(stringLength):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for i in range(stringLength))
