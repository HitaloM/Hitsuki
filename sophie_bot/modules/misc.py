from sophie_bot import BOT_NICK
from sophie_bot.events import register
from sophie_bot.modules.language import get_string
from sophie_bot.modules.flood import flood_limit
from sophie_bot.modules.users import get_user, user_link


@register(incoming=True, pattern="^[/!]id ?(@{})?(.*)".format(BOT_NICK))
async def id(event):

    if await flood_limit(event, 'id') is False:
        return

    text = get_string("misc", "your_id", event.chat_id).format(event.from_id)
    text += get_string("misc", "chat_id", event.chat_id).format(event.chat_id)

    if event.message.reply_to_msg_id:
        msg = await event.get_reply_message()
        userl = await user_link(msg.from_id)
        text += get_string("misc", "user_id", event.chat_id).format(userl, msg.from_id)

    elif len(event.message.raw_text) == 3:
        await event.reply(text)
        return

    else:
        user = await get_user(event)
        userl = await user_link(user['user_id'])
        text += get_string("misc", "user_id", event.chat_id).format(userl, user['user_id'])

    await event.reply(text)
