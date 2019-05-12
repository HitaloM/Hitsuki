from sophie_bot.events import flood_limit, register
from sophie_bot.modules.users import get_user, user_link


@register(incoming=True, pattern="^[/!]id ?(.*)")
async def id(event):

    res = flood_limit(event.chat_id, 'id')
    if res == 'EXIT':
        return
    elif res is True:
        await event.reply('**Flood detected! **\
Please wait 3 minutes before using this command')
        return

    text = "Your id: `{}`\n".format(event.from_id)
    text += "Chat id: `{}`\n".format(event.chat_id)

    if event.message.reply_to_msg_id:
        msg = await event.get_reply_message()
        userl = await user_link(msg.from_id)
        text += "{}'s user id: `{}`\n".format(userl, msg.from_id)

    elif len(event.message.raw_text) == 3:
        await event.reply(text)
        return

    else:
        user = await get_user(event)
        userl = await user_link(user['user_id'])
        text += "{} user id - `{}`\n".format(userl, user['user_id'])

    await event.reply(text)
