from sophie_bot import decorator
from sophie_bot.modules.language import get_string
from sophie_bot.modules.users import is_user_admin
from sophie_bot.modules.helper_func.bot_rights import bot_have_del_msgs_rights


@decorator.command("purge")
@bot_have_del_msgs_rights
async def purge(event):
    K = await is_user_admin(event.chat_id, event.from_id)
    if K is False:
        await event.reply(get_string("msg_deleting", "no_rights_purge", event.chat_id))
        return
    if not event.message.reply_to_msg_id:
        await event.reply(get_string("msg_deleting", "reply_to_msg", event.chat_id))
        return
    msg = await event.get_reply_message()

    chat = await event.get_input_chat()
    msgs = []
    msg_id = msg.id
    delete_to = event.message.id - 1
    await event.client.delete_messages(chat, event.message.id)
    msgs.append(event.reply_to_msg_id)
    for m_id in range(int(delete_to), msg_id - 1, -1):
        msgs.append(m_id)
        if len(msgs) == 100:
            await event.client.delete_messages(chat, msgs)
            msgs = []

    await event.client.delete_messages(chat, msgs)
    await event.reply(get_string("msg_deleting", "purge_done", event.chat_id))


@decorator.command("del")
@bot_have_del_msgs_rights
async def del_message(event):
    K = await is_user_admin(event.chat_id, event.from_id)
    if K is False:
        await event.reply(get_string("msg_deleting", "no_rights_del", event.chat_id))
        return
    msg = await event.get_reply_message()
    chat = await event.get_input_chat()
    msgs = [msg, event.message]
    await event.client.delete_messages(chat, msgs)
