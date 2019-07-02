import ujson

from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import (ChannelParticipantsAdmins,
                               MessageEntityMentionName)

from sophie_bot import BOT_ID, OWNER_ID, SUDO, tbot, decorator, logger, mongodb, redis
from sophie_bot.modules.helper_func.flood import flood_limit, flood_limit_dec


@decorator.BotDo()
async def do_update_users(event):
    await update_users(event)


async def update_users(event):
    chat_id = event.chat_id
    user_id = event.from_id

    if user_id == BOT_ID:
        return

    user = await tbot.get_entity(user_id)
    chat = await tbot.get_entity(chat_id)

    old_chat = mongodb.chat_list.find_one({'chat_id': chat_id})
    old_user = mongodb.user_list.find_one({'user_id': user_id})

    new_chat = []
    new_chat.append(chat_id)

    if old_user:
        if 'chats' in old_user:
            new_chat = old_user['chats']
            if not new_chat or chat_id not in new_chat:
                new_chat.append(chat_id)

    print(new_chat)

    if not hasattr(chat, 'username'):
        chatnick = None
    else:
        chatnick = chat.username

    # Chats with no title is pm
    if hasattr(chat, 'title'):
        chat_new = {
            "chat_id": chat_id,
            "chat_title": chat.title,
            "chat_nick": chatnick
        }

        if old_chat:
            mongodb.chat_list.update_one({'_id': old_chat['_id']}, {"$set": chat_new}, upsert=False)
        else:
            mongodb.chat_list.insert_one(chat_new)
        logger.debug(f"chat {chat_id} updated")

    if user.username:
        username = user.username.lower()
    else:
        username = None

    user_new = {
        'user_id': user_id,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'username': username,
        'user_lang': user.lang_code,
        'chats': new_chat
    }

    logger.debug(f"Updating {user_id}...")
    logger.debug(f"old={old_user}")
    logger.debug(f"new={user_new}")

    if old_user:
        mongodb.user_list.update_one({'_id': old_user['_id']}, {"$set": user_new}, upsert=False)
    else:
        mongodb.user_list.insert_one(user_new)
    logger.debug(f"user {user_id} updated")

    if event.message.reply_to_msg_id:
        msg = await event.get_reply_message()
        user_id = msg.from_id
        user = await tbot.get_entity(user_id)
        old_user = mongodb.user_list.find_one({'user_id': user_id})
        if user.username:
            username = user.username.lower()
        else:
            username = None
        new_chat = [chat_id]
        if old_user:
            if 'chats' in old_user:
                new_chat = old_user['chats']
                if chat_id not in new_chat:
                    new_chat.append(chat_id)
        new_user = {
            'user_id': user_id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': username,
            'user_lang': user.lang_code,
            'chats': new_chat
        }
        logger.debug(f"Updating {user_id}...")
        logger.debug(f"old={old_user}")
        logger.debug(f"new={new_user}")
        if old_user:
            mongodb.user_list.update_one({'_id': old_user['_id']}, {"$set": user_new}, upsert=False)
        else:
            mongodb.user_list.insert_one(user_new)
        logger.debug(f"replied user {user_id} updated")

    if event.message.fwd_from:
        user_id = event.message.fwd_from.from_id
        if not user_id:  # If forwarded from deleted account
            return
        user = await tbot.get_entity(user_id)
        old_user = mongodb.user_list.find_one({'user_id': user_id})
        if user.username:
            username = user.username.lower()
        else:
            username = None
        new_chat = None
        if old_user:
            if 'chats' in old_user:
                new_chat = old_user['chats']

        new_user = {
            'user_id': user_id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': username,
            'user_lang': user.lang_code,
            'chats': new_chat
        }
        logger.debug(f"Updating {user_id}...")
        logger.debug(f"old={old_user}")
        logger.debug(f"new={new_user}")
        if old_user:
            mongodb.user_list.update_one({'_id': old_user['_id']}, {"$set": user_new}, upsert=False)
        else:
            mongodb.user_list.insert_one(new_user)
        logger.debug(f"forwarded user {user_id} updated")


async def update_admin_cache(chat_id):
    admin_list = await tbot.get_participants(
        int(chat_id), filter=ChannelParticipantsAdmins())
    admins = []
    for admin in admin_list:
        admins.append(admin.id)
    dump = ujson.dumps(admins)
    redis.set('admins_cache_{}'.format(chat_id), dump)
    redis.expire('admins_cache_{}'.format(chat_id), 3600)


async def is_user_admin(chat_id, user_id):
    # User's pm should have admin rights

    if user_id in SUDO:
        return True

    if chat_id == user_id:
        return True

    admins = await get_chat_admins(chat_id)
    if user_id in admins:
        return True
    else:
        return False


async def check_group_admin(event, user_id, no_msg=False):
    if hasattr(event, 'chat_id'):
        chat_id = event.chat_id
    elif hasattr(event, 'chat'):
        chat_id = event.chat.id
    if await is_user_admin(chat_id, user_id) is True:
        return True
    else:
        if no_msg is False:
            if await flood_limit(event, "admin-check") is True:
                await event.reply("You should be a admin to do it!")
        return False


async def get_chat_admins(chat_id):
    dump = redis.get('admins_cache_{}'.format(chat_id))
    if not dump:
        await update_admin_cache(chat_id)
        dump = redis.get('admins_cache_{}'.format(chat_id))

    admins = ujson.decode(dump)
    return admins


@decorator.t_command("adminlist")
@flood_limit_dec("adminlist")
async def event(event):
    msg = await event.reply("Updating cache now...")
    await update_admin_cache(event.chat_id)
    dump = redis.get('admins_cache_{}'.format(event.chat_id))
    admins = ujson.decode(dump)
    text = '**Admin in this group:**\n'
    for admin in admins:
        H = mongodb.user_list.find_one({'user_id': admin})
        if H:
            text += '- {} ({})\n'.format(await user_link(H['user_id']), H['user_id'])

    await msg.edit(text)


async def get_user_and_text(event, send_text=True):
    msg = event.message.raw_text.split()
    user = await get_user(event, send_text=send_text)
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


async def get_user(event, send_text=True):
    msg = event.message.raw_text.split()
    user = None
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
                    user = await add_user_to_db(user)
            except Exception as err:
                logger.error(err)
    else:
        if len(msg) > 1:
            arg_user = msg[1]
        else:
            # Wont tagged any user, lets use sender
            user = mongodb.user_list.find_one({'user_id': event.from_id})
            return user
        input_str = event.pattern_match.group(1)
        mention_entity = event.message.entities

        if input_str and input_str.isdigit():
            input_str = int(input_str)

        # Search user in database
        if '@' in arg_user:
            # Remove '@'
            username = arg_user[1:].lower()
            user = mongodb.user_list.find_one({
                'username': username
            })
        elif arg_user.isdigit():
            # User id
            arg_user = int(arg_user)
            user = mongodb.user_list.find_one(
                {'user_id': int(arg_user)}
            )
        else:
            user = mongodb.user_list.find_one(
                {'username': input_str}
            )

        # If we didn't find user in database will ask Telegram.
        if not user:
            try:
                user = await add_user_to_db(await tbot(GetFullUserRequest(arg_user)))
            except (ValueError, TypeError) as err:
                logger.debug(f"cant update user E2: {err}")

        # Still didn't find? Lets try get entities
        try:
            if mention_entity:
                if len(mention_entity) > 1:
                    probable_user_mention_entity = mention_entity[1]
                else:
                    probable_user_mention_entity = mention_entity[0]
                if not user:
                    if not isinstance(probable_user_mention_entity, MessageEntityMentionName):
                        user_id = await event.client.get_entity(input_str)
                    else:
                        user_id = probable_user_mention_entity.user_id
                    if user_id:
                        userf = await event.client(GetFullUserRequest(int(user_id)))
                        user = mongodb.user_list.find_one(
                            {'user_id': int(userf.user.id)}
                        )
                        if not user and userf:
                            user = await add_user_to_db(userf)
        except (ValueError, TypeError) as err:
            logger.debug(f"cant update user E3: {err}")

        if not user:
            # Last try before fail
            try:
                user = await event.client.get_entity(input_str)
                if user:
                    user = await add_user_to_db(user)
            except (ValueError, TypeError) as err:
                logger.debug(f"cant update user E4: {err}")

    if not user and send_text is True:
        await event.reply("I can't find this user in whole Telegram.")

    if not user:
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

    user = await tbot(GetFullUserRequest(data))
    return user


async def user_link(user_id):
    user = mongodb.user_list.find_one({'user_id': user_id})
    if not user:
        try:
            user = await add_user_to_db(await tbot(GetFullUserRequest(int(user_id))))
            user_link = "[{}](tg://user?id={})".format(
                user['first_name'], user['user_id'])
        except Exception:
            user_link = "[{}](tg://user?id={})".format(
                user_id, user_id)
    else:
        user_link = "[{}](tg://user?id={})".format(
            user['first_name'], user['user_id'])

    return user_link


def user_admin_dec(func):
    async def wrapped(event):

        if hasattr(event, 'from_id'):
            user_id = event.from_id
        elif hasattr(event, 'from_user'):
            user_id = event.from_user.id

        if await check_group_admin(event, user_id, no_msg=True) is False:
            await event.reply("You should be admin to do it!")
            return
        return await func(event)
    return wrapped


def user_sudo_dec(func):
    async def wrapped(event):
        if event.from_id not in SUDO:
            return
        return await func(event)
    return wrapped


def user_owner_dec(func):
    async def wrapped(message):
        if not message['from']['id'] == OWNER_ID:
            return
        return await func(message)
    return wrapped
