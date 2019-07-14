from telethon.tl.types import MessageActionChatMigrateTo

from sophie_bot import decorator, mongodb


@decorator.RawAction()
async def migrator(event):
    if hasattr(event, "message") and isinstance(event.message.action, MessageActionChatMigrateTo):
        print('h')
        old_id = event.message.to_id.chat_id
        o_id = '-' + str(old_id)
        new_id = event.message.action.channel_id
        n_id = '-100' + str(new_id)
        print(n_id)

        # Migrating db data

        old = mongodb.chat_list.find_one({'chat_id': int(o_id)})
        if old:
            mongodb.chat_list.update_one({'_id': old['_id']}, {'$set': {'chat_id': int(n_id)}})

        # Migrating notes

        notes = mongodb.notes.find({'chat_id': int(o_id)})
        for note in notes:
            mongodb.notes.update_one({'_id': note['_id']}, {'$set': {'chat_id': int(n_id)}})

        # TODO(Add more datas)
