import re
import ujson

from sophie_bot import MONGO, REDIS
from sophie_bot.events import flood_limit, register
from sophie_bot.modules.users import is_user_admin
from sophie_bot.modules.notes import send_note
from sophie_bot.modules.connections import get_conn_chat


@register(incoming=True)
async def event(event):
    cache = REDIS.get('filters_cache_{}'.format(event.chat_id))
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
            if match:

                regx = '{}'.format(filter)
                H = MONGO.filters.find_one(
                    {'chat_id': event.chat_id,
                     "handler": {'$regex': regx}})

                if H['action'] == 'note':
                    res = flood_limit(
                        event.chat_id, 'filter_handler_{}'.format(filter))
                    if res == 'EXIT':
                        return
                    elif res is True:
                        await event.reply('**Flood detected! **\
Please wait 3 minutes before using this filter')
                        return

                    await send_note(
                        event.chat_id, event.chat_id, event.message.id,
                        H['arg'], show_none=True)

                elif H['action'] == 'delete':
                    await event.delete()


@register(incoming=True, pattern="^/filter(?!s) (.*)")
async def event(event):

    K = await is_user_admin(event.chat_id, event.from_id)
    if K is False:
        await event.reply("You don't have rights to save filters here!")
        return

    args = event.message.raw_text.split(" ")
    if len(args) < 3:
        await event.reply("args error")
        return

    handler = args[1]
    action = args[2]
    if len(args) > 3:
        arg = args[3]
    else:
        arg = None
    text = "Filter added\n"
    text += "keyword: **{}**\n".format(handler)
    if action == 'note':
        if not len(args) > 3:
            await event.reply(
                "Please write in arguments what note "
                "you wanna send on this filter")
            return
        text += "Action: **send note** `{}`".format(arg)
    elif action == 'tmute':
        if not len(args) > 3:
            await event.reply(
                "Please write in arguments on what time you want mute user")
            return
        text += "Action: **temrotary mute sender for** `{}`".format(str(arg))
    elif action == 'delete':
        text += "Action: **delete message**"
    elif action == 'ban':
        text += "Action: **ban sender**"
    elif action == 'mute':
        text += "Action: **mute sender**"
    elif action == 'kick':
        text += "Action: **kick sender**"
    else:
        await event.reply("Wrong action! Read the help.")
        return

    MONGO.filters.insert_one(
        {"chat_id": event.chat_id,
         "handler": handler.lower(),
         'action': action, 'arg': arg})
    update_handlers_cache(event.chat_id)
    await event.reply(text)


@register(incoming=True, pattern="^/filters")
async def event(event):

    res = 2  # flood_limit(event.chat_id, 'filters')
    if res == 'EXIT':
        return
    elif res is True:
        await event.reply('**Flood detected! **\
Please wait 3 minutes before using this command')
        return

    conn = await get_conn_chat(event.from_id, event.chat_id)
    if not conn[0] is True:
        await event.reply(conn[1])
        return
    else:
        chat_id = conn[1]
        chat_title = conn[2]

    filters = MONGO.filters.find({'chat_id': chat_id})
    text = "**Filters in {}:**\n".format(chat_title)
    H = 0
    for filter in filters:
        H += 1
        if filter['arg']:
            text += "- {} ({} - `{}`)\n".format(
                filter['handler'], filter['action'], filter['arg'])
        else:
            text += "- {} ({})\n".format(filter['handler'], filter['action'])
    if H == 0:
        text = 'No filters in **{}**!'.format(chat_title)
    await event.reply(text)


@register(incoming=True, pattern="^/stop")
async def event(event):
    K = await is_user_admin(event.chat_id, event.from_id)
    if K is False:
        await event.reply("You don't have rights to stop filters here!")
        return

    handler = event.message.raw_text.split(" ")[1]
    regx = '{}'.format(handler)
    filter = MONGO.filters.find_one({'chat_id': event.chat_id,
                                     "handler": {'$regex': regx}})
    if not filter:
        await event.reply("I can't find this filter!")
        return
    MONGO.filters.delete_one({'_id': filter['_id']})
    update_handlers_cache(event.chat_id)
    await event.reply("Filter {} deleted!".format(handler))


def update_handlers_cache(chat_id):
    filters = MONGO.filters.find({'chat_id': chat_id})
    lst = []
    for filter in filters:
        lst.append(filter['handler'])
    dump = ujson.dumps(lst)
    REDIS.set('filters_cache_{}'.format(chat_id), dump)
