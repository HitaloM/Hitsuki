import requests
from sophie_bot import decorator, TOKEN
from sophie_bot.modules.helper_func.flood import flood_limit_dec
from sophie_bot.modules.language import get_string
from sophie_bot.modules.users import get_user, user_link, user_admin_dec
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


@decorator.command("pin", arg=True)
@user_admin_dec
async def pinMessage(event):
    tagged_message = await event.get_reply_message()
    if not tagged_message:
        await event.reply(get_string('misc', 'no_reply_msg', event.chat_id))
        return
    msg_2_pin = tagged_message.id
    base_url = 'https://api.telegram.org/bot{}/pinChatMessage'.format(TOKEN)
    data = {'chat_id': event.chat_id, 'message_id': msg_2_pin}
    chk = event.pattern_match.group(1)
    args = chk.lower()
    tru_txt = ['loud', 'notify']
    if args in tru_txt:
        d1 = {'disable_notification': False}  # Thats How mafia Works! :P
        data.update(d1)
    else:
        d1 = {'disable_notification': True}
        data.update(d1)
    requests.post(base_url, data)  # TODO: catch error | Wait for telethon support pin :D
# CatchError=bot API throw error{error: chat_not_modified}[not in shell] if pin on already pined msg
    await event.reply(get_string('misc', 'pinned_success', event.chat_id))


@decorator.command("unpin")
async def unpinMessage(event):
    base_url = 'https://api.telegram.org/bot{}/unpinChatMessage'.format(TOKEN)
    data = {'chat_id': event.chat_id}
    requests.post(base_url, data)  # TODO: CatchError
    await event.reply(get_string('misc', 'unpin_success', event.chat_id))
