from sophie_bot import MONGO

from sophie_bot.modules.users import get_user, user_link
from sophie_bot.events import flood_limit, register


@register(incoming=True, pattern="^/id ?(.*)")
async def event(event):

    res = flood_limit(event.chat_id, 'id')
    if res == 'EXIT':
        return
    elif res is True:
        await event.reply('**Flood detected! **\
Please wait 3 minutes before using this command')
        return

    text = "**ID's:**\n"
    text += "Your id - `{}`\n".format(event.from_id)
    text += "Chat id - `{}`\n".format(event.chat_id)
    text += "Your message id - `{}`\n".format(event.message.id)

    if event.message.reply_to_msg_id:
        msg = await event.get_reply_message()
        text += "\n**Replied message:**\n"
        user = MONGO.user_list.find_one({'user_id': msg.from_id})
        userl = await user_link(msg.from_id)
        text += "{}'s user id - `{}`\n".format(userl, msg.from_id)
        text += "{}'s message id - `{}`".format(userl, msg.id)

    elif event.message.raw_text == "/id":
        await event.reply(text)
        return

    else:
        user = await get_user(event)
        userl = "[{}](https://t.me/{})'s".format(user['first_name'], user['user_id'])
        text += "{} user id - `{}`\n".format(userl, user['user_id'])

    await event.reply(text)
