import re

from sophie_bot import mongodb, redis
from sophie_bot.events import command, register
from sophie_bot.modules.connections import get_conn_chat
from sophie_bot.modules.flood import flood_limit
from sophie_bot.modules.language import get_string
from sophie_bot.modules.notes import send_note
from sophie_bot.modules.users import is_user_admin

import ujson


@register(incoming=True)
async def check_message(event):
    cache = redis.get('filters_cache_{}'.format(event.chat_id))
    try:
        lst = ujson.decode(cache)
    except TypeError:
        return
    if not lst:
        return
    text = event.text.split(" ")
    for filter in lst:
        for word in text:
            match = re.fullmatch(filter, word, flags=re.IGNORECASE)
            if not match:
                return
            H = mongodb.filters.find_one(
                {'chat_id': event.chat_id, "handler": {'$regex': str(filter)}})

            if H['action'] == 'note':
                if await flood_limit(event, 'filter_handler_{}'.format(filter)) is False:
                    return
                await send_note(event.chat_id, event.chat_id, event.message.id,
                                H['arg'], show_none=True)
            elif H['action'] == 'delete':
                await event.delete()


@command("filter(?!s)", arg=True)
async def add_filter(event):
    real_chat_id = event.chat_id
    K = await is_user_admin(event.chat_id, event.from_id)
    if K is False:
        await event.reply(get_string("filters", "dont_have_right", real_chat_id))
        return
    args = event.message.raw_text.split(" ")
    if len(args) < 3:
        await event.reply("args error")
        return
    status, chat_id, chat_title = await get_conn_chat(
        event.from_id, event.chat_id, only_in_groups=True)
    if status is False:
        await event.reply(chat_id)
        return

    handler = args[1]
    action = args[2]
    if len(args) > 3:
        arg = args[3]
    else:
        arg = None
    text = get_string("filters", "filter_added", real_chat_id)
    text += get_string("filters", "filter_keyword", real_chat_id).format(handler)
    if action == 'note':
        if not len(args) > 3:
            await event.reply(get_string("filters", "no_arg_note", real_chat_id))
            return
        text += get_string("filters", "a_send_note", real_chat_id).format(arg)
    elif action == 'tban':
        if not len(args) > 3:
            await event.reply(get_string("filters", "no_arg_tban", real_chat_id))
            return
        text += get_string("filters", "no_arg_tban", real_chat_id).format(str(arg))
    elif action == 'delete':
        text += get_string("filters", "a_del", real_chat_id)
    elif action == 'ban':
        text += get_string("filters", "a_ban", real_chat_id)
    elif action == 'mute':
        text += get_string("filters", "a_mute", real_chat_id)
    elif action == 'kick':
        text += get_string("filters", "a_kick", real_chat_id)
    else:
        await event.reply(get_string("filters", "wrong_action", real_chat_id))
        return

    mongodb.filters.insert_one(
        {"chat_id": chat_id,
         "handler": handler.lower(),
         'action': action, 'arg': arg})
    update_handlers_cache(chat_id)
    await event.reply(text)


@command("filters", arg=True)
async def list_filters(event):
    if await flood_limit(event, 'filters') is False:
        return
    conn = await get_conn_chat(event.from_id, event.chat_id)
    if not conn[0] is True:
        await event.reply(conn[1])
        return
    else:
        chat_id = conn[1]
        chat_title = conn[2]
    filters = mongodb.filters.find({'chat_id': chat_id})
    text = get_string("filters", "filters_in", event.chat_id).format(chat_title)
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


@command("stop", arg=True)
async def stop_filter(event):
    K = await is_user_admin(event.chat_id, event.from_id)
    if K is False:
        await event.reply(get_string("filters", "no_rights_stop", event.chat_id))
        return
    status, chat_id, chat_title = await get_conn_chat(
        event.from_id, event.chat_id, admin=True, only_in_groups=True)

    handler = event.pattern_match.group(2)
    filter = mongodb.filters.find_one({'chat_id': chat_id,
                                      "handler": {'$regex': str(handler)}})
    if not filter:
        await event.reply(get_string("filters", "cant_find_filter", event.chat_id))
        return
    mongodb.filters.delete_one({'_id': filter['_id']})
    update_handlers_cache(chat_id)
    await event.reply(get_string("filters", "filter_deleted", event.chat_id).format(
        filter=handler, chat_name=chat_title))


def update_handlers_cache(chat_id):
    filters = mongodb.filters.find({'chat_id': chat_id})
    lst = []
    for filter in filters:
        lst.append(filter['handler'])
    dump = ujson.dumps(lst)
    redis.set('filters_cache_{}'.format(chat_id), dump)
