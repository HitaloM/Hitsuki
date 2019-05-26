from sophie_bot import bot, mongodb, decorator
from sophie_bot.modules.connections import get_conn_chat
from sophie_bot.modules.helper_func.flood import flood_limit
from sophie_bot.modules.language import get_string
from sophie_bot.modules.notes import send_note
from sophie_bot.modules.users import user_link, user_admin_dec


@decorator.ChatAction()
async def welcome_trigger(event):
    if event.user_joined is True or event.user_added is True:
        chat = event.chat_id
        chat = mongodb.chat_list.find_one({'chat_id': int(chat)})

        user_id = event.action_message.from_id
        bot_id = await bot.get_me()
        if bot_id.id == user_id:
            return  # Do not welcome yourselve
        chat_id = event.action_message.chat_id
        welcome = mongodb.welcomes.find_one({'chat_id': chat_id})
        cleaner = mongodb.clean_service.find({'chat_id': chat})
        if cleaner:
            await event.delete()
        if not welcome:
            await event.reply(get_string("greetings", "welcome_hay", chat))
        elif welcome['enabled'] is False:
            return
        else:
            user = mongodb.user_list.find_one({'user_id': user_id})
            if not user:
                return  # TODO: Add user in db
            if 'last_name' in user:
                last_name = user['last_name']
                if not last_name:
                    last_name = ""
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


@decorator.command("setwelcome", arg=True)
async def setwelcome(event):
    if not event.pattern_match.group(1):
        return
    status, chat_id, chat_title = await get_conn_chat(event.from_id, event.chat_id, admin=True)
    chat = event.chat_id
    chat = mongodb.chat_list.find_one({'chat_id': int(chat)})
    if status is False:
        await event.reply(chat_id)
        return
    note_name = event.pattern_match.group(1)
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


@decorator.command("setwelcome")
async def setwelcome_withot_args(event):
    chat = event.chat_id
    chat = mongodb.chat_list.find_one({'chat_id': int(chat)})
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


@decorator.command('cleanservice', arg=True)
@user_admin_dec
async def cleanservice(event):
    args = event.pattern_match.group(1)
    chat_id = event.chat_id
    enable = ['yes', 'on', 'enable']
    disable = ['no', 'disable']
    bool = args.lower()
    old = mongodb.clean_service.find_one({'chat_id': chat_id})
    if bool:
        if bool in enable:
            new = {'chat_id': chat_id, 'service': True}
            if old:
                mongodb.clean_service.update_one({'_id': old['_id']}, {"$set": new}, upsert=False)
            else:
                mongodb.clean_service.insert_one(new)
            await event.reply(get_string("greetings", "serv_yes", chat_id))
        elif bool in disable:
            mongodb.clean_service.delete_one({'_id': old['_id']})
            await event.reply(get_string("greetings", "serv_no", chat_id))
        else:
            await event.reply(get_string("greetings", "no_args_serv", chat_id))
            return
    else:
        await event.reply(get_string("greetings", "no_args_serv", chat_id))
        return
