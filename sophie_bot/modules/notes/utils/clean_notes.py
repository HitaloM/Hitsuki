from contextlib import suppress

from telethon.errors.rpcerrorlist import MessageDeleteForbiddenError

from sophie_bot.services.mongo import db
from sophie_bot.services.telethon import tbot


def clean_notes(func):
    async def wrapped_1(*args, **kwargs):
        event = args[0]

        message = await func(*args, **kwargs)
        if not message:
            return

        if event.chat.type == 'private':
            return

        chat_id = event.chat.id

        data = await db.clean_notes.find_one({'chat_id': chat_id})
        if not data:
            return

        if data['enabled'] is not True:
            return

        if 'msgs' in data:
            with suppress(MessageDeleteForbiddenError):
                await tbot.delete_messages(chat_id, data['msgs'])

        msgs = []
        if hasattr(message, 'message_id'):
            msgs.append(message.message_id)
        else:
            msgs.append(message.id)

        msgs.append(event.message_id)

        await db.clean_notes.update_one({'chat_id': chat_id}, {'$set': {'msgs': msgs}})

    return wrapped_1
