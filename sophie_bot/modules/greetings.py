from sophie_bot import bot, mongodb
from sophie_bot.events import register
from sophie_bot.modules.connections import get_conn_chat
from sophie_bot.modules.notes import send_note
from sophie_bot.modules.users import user_link
from sophie_bot.modules.flood import flood_limit

from telethon import events


@bot.on(events.ChatAction)
async def handler(event):
    print(event)
    if event.user_joined is True or event.user_added is True:
        user_id = event.action_message.from_id
        bot_id = await bot.get_me()
        if bot_id.id == user_id:
            return  # Do not welcome yourselve
        chat_id = event.action_message.chat_id
        welcome = mongodb.welcomes.find_one({'chat_id': chat_id})
        if not welcome:
            await event.reply("Welcome! How are you?")
        elif welcome['enabled'] is False:
            return
        else:
            user = mongodb.user_list.find_one({'user_id': user_id})
            if not user['last_name']:
                last_name = None
                full_name = user['first_name']
            else:
                last_name = user['last_name']
                full_name = user['first_name'] + " " + last_name

            if not user['username']:
                username = None
            else:
                username = user['username']

            chatname = mongodb.chat_list.find_one({'chat_id': chat_id})

            text = welcome['note'].format(
                first=user['first_name'],
                last=last_name,
                fullname=full_name,
                username=username,
                mention=await user_link(user_id),
                id=user_id,
                chatname=chatname['chat_title'],
                rules='Will be later'
            )
            await send_note(
                event.chat_id, chat_id, event.action_message.id, text, show_none=True)


@register(incoming=True, pattern="^[/!]setwelcome (.*)")
async def setwelcome(event):
    status, chat_id, chat_title = await get_conn_chat(event.from_id, event.chat_id, admin=True)
    if status is False:
        await event.reply(chat_id)
        return
    note_name = event.pattern_match.group(1)
    note = mongodb.notes.find_one({
        'chat_id': chat_id,
        'name': note_name
    })
    if not note:
        await event.reply("I can't find this note")
        return
    old = mongodb.welcomes.find_one({'chat_id': chat_id})
    if old:
        mongodb.welcomes.delete_one({'_id': old['_id']})
    mongodb.welcomes.insert_one({
        'chat_id': chat_id,
        'enabled': True,
        'note': note_name
    })
    await event.reply("Welcome set to note: `{}`".format(note_name))


@register(incoming=True, pattern="^[/!]setwelcome$")
async def setwelcome(event):
    if await flood_limit(event, 'setwelcome') is False:
        return
    status, chat_id, chat_title = await get_conn_chat(event.from_id, event.chat_id, only_in_groups=True)
    if status is False:
        await event.reply(chat_id)
        return
    old = mongodb.welcomes.find_one({'chat_id': chat_id})
    if old:
        note_name = old['note']
        await event.reply("Welcome is note: `{}`".format(note_name))
    else:
        await event.reply("Welcome is default")

