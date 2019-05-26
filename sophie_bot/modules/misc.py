from sophie_bot import decorator
from sophie_bot.modules.helper_func.flood import flood_limit_dec
from sophie_bot.modules.language import get_string
from sophie_bot.modules.users import get_user, user_link
from sophie_bot.modules.disable import disablable_dec


@decorator.command("id", arg=True)
@disablable_dec("id")
@flood_limit_dec("id")
async def id(event):
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
