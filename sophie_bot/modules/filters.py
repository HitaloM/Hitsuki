import re

from telethon.tl.custom import Button

from sophie_bot import decorator, mongodb, redis, WHITELISTED
from sophie_bot.modules.connections import connection, get_conn_chat
from sophie_bot.modules.disable import disablable_dec
from sophie_bot.modules.helper_func.flood import flood_limit_dec
from sophie_bot.modules.language import get_string, get_strings_dec
from sophie_bot.modules.notes import send_note, button_parser
from sophie_bot.modules.bans import ban_user, kick_user
from sophie_bot.modules.users import user_admin_dec, user_link, get_chat_admins
from sophie_bot.modules.warns import randomString


@decorator.insurgent()
async def check_message(event):
    filters = redis.lrange('filters_cache_{}'.format(event.chat_id), 0, -1)
    if not filters:
        update_handlers_cache(event.chat_id)
        filters = redis.lrange('filters_cache_{}'.format(event.chat_id), 0, -1)
    if redis.llen('filters_cache_{}'.format(event.chat_id)) == 0:
        return
    text = event.text
    chat = event.chat_id
    user = event.from_id
    for keyword in filters:
        keyword = keyword.decode("utf-8")
        keyword = re.escape(keyword)
        keyword = keyword.replace('\(\+\)', '.*')
        pattern = r"( |^|[^\w])" + keyword + r"( |$|[^\w])"
        if re.search(pattern, text, flags=re.IGNORECASE):
            H = mongodb.filters.find_one(
                {'chat_id': event.chat_id, "handler": {'$regex': str(pattern)}})
            action = H['action']
            if action == 'note':
                await send_note(event.chat_id, event.chat_id, event.message.id,
                                H['arg'], show_none=True)
            elif action == 'answer':
                text, buttons = button_parser(event.chat_id, H['arg'])
                if not buttons:
                    buttons = None
                await event.reply(text, buttons=buttons)
            elif action == 'delete':
                await event.delete()
            elif action == 'ban':
                if await ban_user(event, user, chat, None, no_msg=True) is True:
                    text = get_string('filters', 'filter_ban_success', chat).format(
                        user=await user_link(user),
                        filter=filter
                    )
                    event.reply(text)
            elif action == 'tban':
                if await ban_user(event, user, chat, H['arg'], no_msg=True) is True:
                    text = get_string('filters', 'filter_tban_success', chat).format(
                        user=await user_link(user),
                        time=H['arg'],
                        filter=filter
                    )
                    event.reply(text)
            elif action == 'kick':
                if await kick_user(event, user, chat, no_msg=True) is True:
                    text = get_string('filters', 'filter_kick_success', chat).format(
                        user=await user_link(user),
                        filter=filter
                    )
                    event.reply(text)
            elif action == 'warn':
                user_id = event.sender_id
                if user_id in WHITELISTED:
                    return

                if user_id in await get_chat_admins(chat):
                    return

                warn_limit = mongodb.warnlimit.find_one({'chat_id': chat})
                db_warns = mongodb.warns.find({
                    'user_id': user_id,
                    'group_id': chat
                })

                #  to avoid adding useless another warn in db
                current_warns = 1

                for _ in db_warns:
                    current_warns += 1

                if not warn_limit:
                    warn_limit = 3
                else:
                    warn_limit = int(warn_limit['num'])

                if current_warns >= warn_limit:
                    if await ban_user(event, user_id, chat, None) is False:
                        print(f'cannot ban user {user_id}')
                        return

                    await ban_user(event, user_id, chat, None, no_msg=False)
                    mongodb.warns.delete_many({
                        'user_id': user_id,
                        'group_id': chat
                    })

                    resp = get_string("filters", "filter_warn_ban", event.chat_id).format(warns=warn_limit,
                                                                                          user=await user_link(user),
                                                                                          reason=H['arg'])

                    return await event.reply(resp)
                else:
                    rndm = randomString(15)

                    mongodb.warns.insert_one({
                        'warn_id': rndm,
                        'user_id': user_id,
                        'group_id': chat,
                        'reason': H['arg']
                    })

                    buttons = [Button.inline("⚠️ Remove warn", 'remove_warn_{}'.format(rndm))]
                    rules = mongodb.rules.find_one({"chat_id": chat})

                    if rules:
                        buttons.append(Button.inline("📝 Rules", 'get_note_{}_{}'.format(
                            chat, rules['note']
                        )))

                    status, chat_id, chat_title = await get_conn_chat(event.from_id, event.chat_id,
                                                                      admin=True, only_in_groups=True)

                    resp = get_string("filters", "filter_warn_warned", event.chat_id).format(user=await user_link(user),
                                                                                             chat=chat_title,
                                                                                             current_warns=current_warns,
                                                                                             max_warns=warn_limit,
                                                                                             reason=H['arg'])
                    return await event.reply(resp, buttons=buttons)
            break


@decorator.t_command("filter(?!s)", arg=True)
@flood_limit_dec("filter")
@user_admin_dec
@connection(admin=True)
@get_strings_dec("filters")
async def add_filter(event, strings, status, chat_id, chat_title):
    args = event.message.raw_text.split(" ")
    if len(args) < 3:
        await event.reply(strings["wrong_action"])
        return

    handler = args[1]
    action = args[2]
    if len(args) > 3:
        arg = args[3]
    else:
        arg = None
    text = strings["filter_added"]
    text += strings["filter_keyword"].format(handler)
    if action == 'note':
        if not len(args) > 3:
            await event.reply(strings["no_arg_note"])
            return
        text += strings["a_send_note"].format(arg)
    elif action == 'tban':
        if not len(args) > 3:
            await event.reply(strings["no_arg_tban"])
            return
        text += strings["a_tban"].format(str(arg))
    elif action == 'answer':
        txt = event.message.raw_text.split(" ", 2)[2]
        if len(txt) <= 2:
            await event.reply(strings["wrong_action"])
            return
        arg = txt
        text += strings["a_answer"]
    elif action == 'delete':
        text += strings["a_del"]
    elif action == 'ban':
        text += strings["a_ban"]
    elif action == 'mute':
        text += strings["a_mute"]
    elif action == 'kick':
        text += strings["a_kick"]
    elif action == 'warn':
        raw_text = event.text.split(" ")
        arg = None
        if raw_text[3:]:
            arg = " ".join(raw_text[3:])
        else:
            arg = f"Automatic action on filter:\n{handler.lower()}."

        text += strings["a_warn"].format(arg)
    else:
        await event.reply(strings["wrong_action"])
        return

    mongodb.filters.insert_one({
        "chat_id": chat_id,
        "handler": handler.lower(),
        "action": action,
        "arg": arg
    })
    update_handlers_cache(chat_id)
    await event.reply(text)


@decorator.t_command("filters", arg=True)
@disablable_dec("filters")
@flood_limit_dec("filters")
@connection()
async def list_filters(event, status, chat_id, chat_title):
    filters = mongodb.filters.find({'chat_id': chat_id})
    text = get_string("filters", "filters_in", event.chat_id).format(chat_name=chat_title)
    H = 0

    for filter in filters:
        H += 1
        if filter['arg']:
            text += "- {} ({} - `{}`)\n".format(
                filter['handler'], filter['action'], filter['arg'])
        else:
            text += "- {} ({})\n".format(filter['handler'], filter['action'])
    if H == 0:
        text = get_string("filters", "no_filters_in", event.chat_id).format(chat_title)
    await event.reply(text)


@decorator.t_command("stop", arg=True)
@user_admin_dec
@connection(admin=True)
async def stop_filter(event, status, chat_id, chat_title):
    handler = event.message.text.split(" ", 2)[1]
    filter = mongodb.filters.find_one({'chat_id': chat_id,
                                      "handler": {'$regex': str(handler)}})
    if not filter:
        await event.reply(get_string("filters", "cant_find_filter", event.chat_id))
        return
    mongodb.filters.delete_one({'_id': filter['_id']})
    update_handlers_cache(chat_id)
    text = str(get_string("filters", "filter_deleted", event.chat_id))
    text = text.format(filter=filter['handler'], chat_name=chat_title)
    await event.reply(text)


def update_handlers_cache(chat_id):
    filters = mongodb.filters.find({'chat_id': chat_id})
    redis.delete('filters_cache_{}'.format(chat_id))
    for filter in filters:
        redis.lpush('filters_cache_{}'.format(chat_id), filter['handler'])
