import random
import string
import re

from telethon import events
from sophie_bot import MONGO, bot, WHITELISTED
from sophie_bot.events import register
from sophie_bot.modules.users import get_user_and_text, is_user_admin
from sophie_bot.modules.bans import ban_user
from telethon.tl.custom import Button


@register(incoming=True, pattern="^/warn(?!s) ?(.*)")
async def event(event):
    K = await is_user_admin(event.chat_id, event.from_id)
    if K is False:
        await event.reply("You don't have rights to warn users here!")
        return

    try:
        user, reason = await get_user_and_text(event)
        user_id = int(user['user_id'])
    except Exception:
        user_id = int(event.from_id)
    chat_id = event.chat_id
    if user_id in WHITELISTED:
        await event.reply("This user is whitelisted!")
        return
    rndm = randomString(15)
    print(rndm)
    MONGO.warns.insert_one({
        'warn_id': rndm,
        'user_id': user_id,
        'group_id': chat_id,
        'reason': str(reason)
    })
    admin_id = event.from_id
    admin = MONGO.user_list.find_one({'user_id': admin_id})
    admin_str = '[{}](@{})'.format(
        admin['first_name'], admin['username'])
    user_str = '[{}](@{})'.format(
        user['first_name'], user['username'])
    text = "{} warned {}\n".format(admin_str, user_str)
    text += "Reason: `{}`\n".format(reason)

    old = MONGO.warns.find({
        'user_id': user_id,
        'group_id': chat_id
    })
    h = 0
    for suka in old:
        h += 1

    button = Button.inline("Remove warn", 'remove_warn_{}'.format(rndm))

    if h >= 3:
        if await ban_user(event, user_id, chat_id, None) is False:
            return
        text += "Max warns limit reached, user banned!"
        MONGO.warns.delete_many({
            'user_id': user_id,
            'group_id': chat_id
        })
    else:
        text += "Warns count - {}/{}\n".format(h, 3)

    await event.reply(text, buttons=button, link_preview=False)


@bot.on(events.CallbackQuery(data=re.compile(b'remove_warn_')))
async def event(event):
    user_id = event.query.user_id
    K = await is_user_admin(event.chat_id, user_id)
    if K is False:
        await event.answer("You don't have rights to remove warns here!")
        return

    warn_id = re.search(r'remove_warn_(.*)', str(event.data)).group(1)[:-1]
    print(warn_id)
    warn = MONGO.warns.find_one({'warn_id': warn_id})
    MONGO.notes.delete_one({'_id': warn['_id']})
    user = MONGO.user_list.find_one({'user_id': user_id})
    user_str = '[{}](@{})'.format(
        user['first_name'], user['username'])
    await event.edit("Warn deleted by {}".format(user_str), link_preview=False)


@register(incoming=True, pattern="^/warns ?(.*)")
async def event(event):
    try:
        user, reason = await get_user_and_text(event)
        user_id = int(user['user_id'])
    except Exception:
        user_id = int(event.from_id)
    if user_id in WHITELISTED:
        await event.reply(
            "This user clear as white paper, he can't have warns."
        )
        return
    warns = MONGO.warns.find({
        'user_id': user_id,
        'group_id': event.chat_id
    })
    user = MONGO.user_list.find_one({'user_id': user_id})
    user_name = user['first_name']
    user_str = '[{}](@{})'.format(
        user['first_name'], user['username'])
    chat_title = MONGO.chat_list.find_one({
        'chat_id': event.chat_id})['chat_title']
    text = "**Warns of {}:**\n".format(user_name)
    H = 0
    for warn in warns:
        H += 1
        rsn = warn['reason']
        if rsn == 'None':
            rsn = "No reason"
        text += "{}: `{}`\n".format(H, rsn)
    if H == 0:
        await event.reply("User {} don't have any warns in **{}**!".format(
            user_str, chat_title))
        return
    await event.reply(text)


def randomString(stringLength):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for i in range(stringLength))
