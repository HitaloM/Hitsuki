import re

from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights

from sophie_bot import WHITELISTED, tbot, decorator, mongodb, redis
from sophie_bot.modules.connections import connection
from sophie_bot.modules.disable import disablable_dec
from sophie_bot.modules.helper_func.flood import t_flood_limit_dec
from sophie_bot.modules.language import get_string, t_get_strings_dec
from sophie_bot.modules.notes import send_note
from sophie_bot.modules.users import is_user_admin, user_admin_dec, user_link


@decorator.insurgent()
async def check_message(event):
    filters = redis.lrange('filters_cache_{}'.format(event.chat_id), 0, -1)
    if not filters:
        update_handlers_cache(event.chat_id)
        filters = redis.lrange('filters_cache_{}'.format(event.chat_id), 0, -1)
    if redis.llen('filters_cache_{}'.format(event.chat_id)) == 0:
        return
    text = event.text.split(" ")
    for filter in filters:
        filter = filter.decode("utf-8")
        for word in text:
            match = re.fullmatch(filter, word, flags=re.IGNORECASE)
            if not match:
                continue
            H = mongodb.filters.find_one(
                {'chat_id': event.chat_id, "handler": {'$regex': str(filter)}})

            if H['action'] == 'note':
                await send_note(event.chat_id, event.chat_id, event.message.id,
                                H['arg'], show_none=True)
            elif H['action'] == 'delete':
                await event.delete()
            elif H['action'] == 'ban':
                await filter_ban(event, filter, None)


@decorator.command("filter(?!s)", arg=True)
@t_flood_limit_dec("filter")
@user_admin_dec
@connection(admin=True)
@t_get_strings_dec("filters")
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
    elif action == 'delete':
        text += strings["a_del"]
    elif action == 'ban':
        text += strings["a_ban"]
    elif action == 'mute':
        text += strings["a_mute"]
    elif action == 'kick':
        text += strings["a_kick"]
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


@decorator.command("filters", arg=True)
@disablable_dec("filters")
@t_flood_limit_dec("filters")
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


@decorator.command("stop", arg=True)
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


async def filter_ban(event, filter, time):
    chat = event.chat_id
    user = event.from_id

    if await is_user_admin(chat, user) is True:
        return

    if int(user) in WHITELISTED:
        return

    bot_id = await tbot.get_me()
    if user == bot_id.id:
        return

    banned_rights = ChatBannedRights(
        until_date=time,
        view_messages=True,
        send_messages=True,
        send_media=True,
        send_stickers=True,
        send_gifs=True,
        send_games=True,
        send_inline=True,
        embed_links=True,
    )

    try:
        await event.client(
            EditBannedRequest(
                chat,
                user,
                banned_rights
            )
        )

    except Exception:
        pass

    text = get_string('filters', 'filter_ban_success', chat).format(user=await user_link(user),
                                                                    filter=filter)
    await tbot.send_message(
        chat,
        text
    )
