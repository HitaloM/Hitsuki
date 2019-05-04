from sophie_bot import mongodb, redis, bot
from sophie_bot.events import flood_limit, register

from telethon.tl.types import ChannelParticipantsAdmins
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import MessageEntityMentionName

import ujson


@register()
async def event(event):
    await update_users(event)


async def update_users(event):
    chat_id = event.chat_id
    user_id = event.from_id
    user = await bot.get_entity(user_id)
    chat = await bot.get_entity(chat_id)

    old_chats = mongodb.chat_list.find({'chat_id': chat_id})
    old_users = mongodb.user_list.find({'user_id': user_id})

    new_chat = [chat_id]

    if old_users:
        for old_user in old_users:
            if 'chats' in old_user:
                new_chat = old_user['chats']
                if chat_id not in new_chat:
                    new_chat.append(chat_id)

            mongodb.user_list.delete_one({'_id': old_user['_id']})
    if old_chats:
        for old_chat in old_chats:
            mongodb.chat_list.delete_one({'_id': old_chat['_id']})

    if not chat.username:
        chatnick = None
    else:
        chatnick = chat.username

    if not hasattr(chat, 'title'):
        chat_name = "Local chat"
    else:
        chat_name = chat.title

    mongodb.chat_list.insert_one(
        {"chat_id": chat_id,
         "chat_title": chat_name,
         "chat_nick": chatnick})
    mongodb.user_list.insert_one(
        {'user_id': user_id,
         'first_name': user.first_name,
         'last_name': user.last_name,
         'username': user.username,
         'user_lang': user.lang_code,
         'chats': new_chat})

    try:
        if event.message.reply_to_msg_id:
            msg = await event.get_reply_message()
            user_id = msg.from_id
            user = await bot.get_entity(user_id)
            old_users = mongodb.user_list.find({'user_id': user_id})
            if old_users:
                for old_user in old_users:
                    mongodb.user_list.delete_one({'_id': old_user['_id']})

            mongodb.user_list.insert_one(
                {'user_id': user_id,
                 'first_name': user.first_name,
                 'last_name': user.last_name,
                 'username': user.username,
                 'user_lang': user.lang_code})
    except Exception as err:
        await event.edit(str(err))


async def update_admin_cache(chat_id):
    admin_list = await bot.get_participants(
        int(chat_id), filter=ChannelParticipantsAdmins())
    admins = []
    for admin in admin_list:
        admins.append(admin.id)
    dump = ujson.dumps(admins)
    redis.set('admins_cache_{}'.format(chat_id), dump)
    redis.expire('admins_cache_{}'.format(chat_id), 3600)


async def is_user_admin(chat_id, user_id):
    # User's pm should have admin rights
    if chat_id == user_id:
        return True
    admins = await get_chat_admins(chat_id)
    if user_id in admins:
        return True
    else:
        return False


async def get_chat_admins(chat_id):
    dump = redis.get('admins_cache_{}'.format(chat_id))
    if not dump:
        await update_admin_cache(chat_id)
        dump = redis.get('admins_cache_{}'.format(chat_id))

    admins = ujson.decode(dump)
    return admins


@register(incoming=True, pattern="^[/!]adminlist|^/admins")
async def event(event):
    res = flood_limit(event.chat_id, 'admins')
    if res == 'EXIT':
        return
    elif res is True:
        await event.reply('**Flood detected! **\
Please wait 3 minutes before using this command')
        return
    msg = await event.reply("Updating cache now...")
    admin_list = await bot.get_participants(
        int(event.chat_id), filter=ChannelParticipantsAdmins())
    text = '**Admin in this group:**\n'
    for admin in admin_list:
        text += '- {} ({})'.format(admin.first_name, admin.id)
        if admin.bot:
            text += " (bot)"
        if admin.creator:
            text += " (creator)"
        text += '\n'

    await msg.edit(text)


async def get_user_and_text(event):
    msg = event.message.raw_text.split()
    user = await get_user(event)
    if event.reply_to_msg_id:
        if len(msg) >= 2:
            text = event.message.raw_text.split(" ", 1)[1]
        else:
            text = None
    else:
        if len(msg) >= 3:
            text = event.message.raw_text.split(" ", 2)[2]
        else:
            text = None

    return user, text


async def get_user(event):
    msg = event.message.raw_text.split()
    if event.reply_to_msg_id:
        msg = await event.get_reply_message()
        user = mongodb.user_list.find_one(
            {'user_id': msg.from_id})

        # Will ask Telegram for help with it.
        if not user:
            try:
                user = await event.client(GetFullUserRequest(int(msg.from_id)))
                # Add user in database
                if user:
                    user = add_user_to_db(user)
            except Exception:
                pass
    else:
        if len(msg) > 1:
            msg_1 = msg[1]
        else:
            # Wont tagged any user, lets use sender
            user = mongodb.user_list.find_one({'user_id': event.from_id})
            return user
        input_str = event.pattern_match.group(1)
        mention_entity = event.message.entities

        if input_str and input_str.isdigit():
            input_str = int(input_str)

        # Search user in database
        if '@' in msg_1:
            # Remove '@'
            user = mongodb.user_list.find_one(
                {'username': msg_1[1:]}
            )
        elif msg_1.isdigit():
            # User id
            msg_1 = int(msg_1)
            user = mongodb.user_list.find_one(
                {'user_id': int(msg_1)}
            )
        else:
            user = mongodb.user_list.find_one(
                {'username': input_str}
            )

        # If we didn't find user in database will ask Telegram.
        if not user:
            try:
                user = await event.client(GetFullUserRequest(msg_1))
                # Add user in database
                user = await add_user_to_db(user)
            except Exception:
                pass

        # Still didn't find? Lets try get entities
        if mention_entity:
            probable_user_mention_entity = mention_entity[1]
            if not user:
                if not isinstance(probable_user_mention_entity, MessageEntityMentionName):
                    user_id = await event.client.get_entity(input_str)
                    return
                else:
                    user_id = probable_user_mention_entity.user_id
                if user_id:
                    userf = await event.client(GetFullUserRequest(int(user_id)))
                    user = mongodb.user_list.find_one(
                        {'user_id': int(userf.user.id)}
                    )
                    if not user and userf:
                        user = await add_user_to_db(userf)

        if not user:
            # Last try before fail
            try:
                user = await event.client.get_entity(input_str)
                if user:
                    user = await add_user_to_db(user)
            except Exception as err:
                await event.reply(str(err))
                return None
    if not user:
        await event.reply("I can't find this user in whole Telegram.")
        return None
    return user


async def add_user_to_db(user):
    user = {'user_id': user.user.id,
            'first_name': user.user.first_name,
            'last_name': user.user.last_name,
            'username': user.user.username,
            'user_lang': user.user.lang_code
            }
    old = mongodb.user_list.find_one({'user_id': user['user_id']})
    if old:
        mongodb.user_list.delete_one({'_id': old['_id']})
    mongodb.user_list.insert_one(user)
    return user


async def get_id_by_nick(data):
    # Check if data is user_id
    user = mongodb.user_list.find_one({'username': data.replace('@', "")})
    if user:
        return user['user_id']

    user = await bot(GetFullUserRequest(data))
    return user


async def user_link(user_id):
    user = mongodb.user_list.find_one({'user_id': user_id})
    user_link = "[{}](tg://user?id={})".format(
        user['first_name'], user['user_id'])
    return user_link
