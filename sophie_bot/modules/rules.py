from aiogram import types

from sophie_bot import decorator, mongodb
from sophie_bot.modules.connections import connection
from sophie_bot.modules.language import get_strings_dec
from sophie_bot.modules.users import user_admin_dec


@decorator.command("setrules")
@user_admin_dec
@connection(only_in_groups=True, admin=True)
@get_strings_dec("rules")
async def setwelcome(message, strings, status, chat_id, chat_title, *args):
    chat = mongodb.chat_list.find_one({'chat_id': int(chat_id)})
    arg = message['text'].split(" ", 2)
    if len(arg) <= 1:
        return
    if status is False:
        await message.reply(chat_id)

    note_name = arg[1]
    off = ['off', 'none', 'disable']
    if note_name in off:
        check = mongodb.rules.delete_one({'chat_id': chat})
        if check:
            text = "Rules deleted for this chat"
        else:
            text = "Rules didn't setuped yet"
        await message.reply(text)
        return
    note = mongodb.notes.find_one({
        'chat_id': chat_id,
        'name': note_name
    })
    if not note:
        await message.reply(strings["cant_find_note"])
        return
    old = mongodb.rules.find_one({'chat_id': chat_id})
    if old:
        mongodb.rules.delete_one({'_id': old['_id']})
    mongodb.rules.insert_one({
        'chat_id': chat_id,
        'note': note_name
    })
    await message.reply(strings["rules_set_to_note"].format(note_name),
                        parse_mode=types.ParseMode.HTML)
