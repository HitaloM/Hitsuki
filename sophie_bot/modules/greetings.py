from sophie_bot import BOT_NICK, bot, mongodb
from sophie_bot.events import register
from sophie_bot.modules.language import get_string
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
            await event.reply(get_string("greetings", "welcome_hay", chat))
        elif welcome['enabled'] is False:
            return
        else:
            user = mongodb.user_list.find_one({'user_id': user_id})
            if 'last_name' in user:
                last_name = user['last_name']
                full_name = user['first_name'] + " " + last_name
            else:
                last_name = None
                full_name = user['first_name']

            if 'username' in user:
                username = user['username']
            else:
                username = None

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


@register(incoming=True, pattern="^[/!]setwelcome ?(@{})?(.*)".format(BOT_NICK))
async def setwelcome(event):
    status, chat_id, chat_title = await get_conn_chat(event.from_id, event.chat_id, admin=True)
    if status is False:
        await event.reply(chat_id)
        return
    note_name = event.pattern_match.group(2)
    note = mongodb.notes.find_one({
        'chat_id': chat_id,
        'name': note_name
    })
    if not note:
        await event.reply(get_string("greetings", "cant_find_note", chat))
        return
    old = mongodb.welcomes.find_one({'chat_id': chat_id})
    if old:
        mongodb.welcomes.delete_one({'_id': old['_id']})
    mongodb.welcomes.insert_one({
        'chat_id': chat_id,
        'enabled': True,
        'note': note_name
    })
    await event.reply(get_string("greetings", "welcome_set_to_note", chat).format(note_name))


@register(incoming=True, pattern="^[/!]setwelcome ?(@{})?(.*)".format(BOT_NICK))
async def setwelcome_withot_args(event):
    if await flood_limit(event, 'setwelcome') is False:
        return
    status, chat_id, chat_title = await get_conn_chat(
        event.from_id, event.chat_id, only_in_groups=True)
    if status is False:
        await event.reply(chat_id)
        return
    old = mongodb.welcomes.find_one({'chat_id': chat_id})
    if old:
        note_name = old['note']
        await event.reply(get_string("greetings", "welcome_is_note", chat).format(note_name))
    else:
        await event.reply(get_string("greetings", "welcome_is_default", chat))
