import ujson
import datetime
import html

from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import (ChannelParticipantsAdmins,
                               MessageEntityMentionName)

from sophie_bot import OWNER_ID, SUDO, tbot, decorator, logger, mongodb, redis
from sophie_bot.modules.helper_func.flood import flood_limit, flood_limit_dec


@decorator.AioBotDo()
async def update_users(message, **kwargs):
    chat_id = message.chat.id

    # Update chat
    new_chat = message.chat
    if not new_chat.type == 'private':

        old_chat = mongodb.chat_list.find_one({'chat_id': chat_id})

        if not hasattr(new_chat, 'username'):
            chatnick = None
        else:
            chatnick = new_chat.username

        if old_chat and 'first_detected_date' in old_chat:
            first_detected_date = old_chat['first_detected_date']
        else:
            print('new chat')
            first_detected_date = datetime.datetime.now()

        chat_new = {
            "chat_id": chat_id,
            "chat_title": html.escape(new_chat.title),
            "chat_nick": chatnick,
            "type": new_chat.type,
            "first_detected_date": first_detected_date
        }

        mongodb.chat_list.update_one({'chat_id': chat_id}, {"$set": chat_new}, upsert=True)

        logger.debug(f"Users: Chat {chat_id} updated")

    # Update users
    update_user(chat_id, message.from_user)

    if "reply_to_message" in message and \
        hasattr(message.reply_to_message.from_user, 'chat_id') and \
            message.reply_to_message.from_user.chat_id:
        update_user(chat_id, message.reply_to_message.from_user)

    if "forward_from" in message:
        update_user(chat_id, message.forward_from)


def update_user(chat_id, new_user):
    old_user = mongodb.user_list.find_one({'user_id': new_user.id})

    new_chat = [chat_id]

    if old_user and 'chats' in old_user:
        if old_user['chats']:
            new_chat = old_user['chats']
        if not new_chat or chat_id not in new_chat:
            new_chat.append(chat_id)

    if old_user and 'first_detected_date' in old_user:
        first_detected_date = old_user['first_detected_date']
    else:
        first_detected_date = datetime.datetime.now()

    if new_user.username:
        username = new_user.username.lower()
    else:
        username = None

    if hasattr(new_user, 'last_name') and new_user.last_name:
        last_name = html.escape(new_user.last_name)
    else:
        last_name = None

    first_name = html.escape(new_user.first_name)

    user_new = {
        'user_id': new_user.id,
        'first_name': first_name,
        'last_name': last_name,
        'username': username,
        'user_lang': new_user.language_code,
        'chats': new_chat,
        'first_detected_date': first_detected_date
    }

    mongodb.user_list.update_one({'user_id': new_user.id}, {"$set": user_new}, upsert=True)

    logger.debug(f"Users: User {new_user.id} updated")

    return user_new


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


async def aio_get_user(message, send_text=True, allow_self=False):
    args = message.text.split(None, 2)
    user = None
    text = None

    # Only 1 way
    if len(args) < 2 and "reply_to_message" in message:
        user = await get_user_by_id(message.reply_to_message.from_user.id)

    # Get all mention entities
    entities = filter(lambda ent: ent['type'] == 'mention', message.entities)
    for item in entities:
        mention = item.get_text(message.text)

        # Allow get user only in second arg: ex. /warn (user) Reason
        # so if we write nick in reason and try warn by reply it will work as expected
        if mention == args[1]:
            if len(args) > 2:
                text = args[2]
            return await get_user_by_username(mention), text

    # Ok, now we really be unsure, so don't return right away
    if len(args) > 1:
        if args[1].isdigit():
            user = await get_user_by_id(args[1])

        # Admin can mess a @
        if not user:
            user = await get_user_by_username(args[1])

    if len(args) > 2:
        text = args[2]

    # Not first because ex. admins can /warn (user) and reply to offended user
    if not user and "reply_to_message" in message:
        if len(args) > 1:
            text = message.get_args()
        return await get_user_by_id(message.reply_to_message.from_user.id), text

    if not user and allow_self is True:
        user = await get_user_by_id(message.from_user.id)

    if not user:
        await message.answer('I can\'t get this user!')
        return None, None

    return user, text


async def get_user_by_username(username):
    # Search username in database
    if '@' in username:
        # Remove '@'
        username = username[1:].lower()
        user = mongodb.user_list.find_one({
            'username': username
        })
    else:
        user = mongodb.user_list.find_one(
            {'username': username}
        )

    # Ohnu, we don't have this user in DB
    if not user:
        try:
            user = await add_user_to_db(await tbot(GetFullUserRequest(username)))
        except (ValueError, TypeError):
            user = None

    return user


async def get_user_by_id(user_id):
    user = mongodb.user_list.find_one(
        {'user_id': int(user_id)}
    )
    # Ohnu, we don't have this user in DB
    if not user:
        try:
            user = await add_user_to_db(await tbot(GetFullUserRequest(int(user_id))))
        except (ValueError, TypeError):
            user = None

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


async def user_link_html(user_id, custom_name=False):
    user = mongodb.user_list.find_one({'user_id': user_id})
    user_name = None

    if user:
        user_name = user['first_name']
    else:
        try:
            user = await add_user_to_db(await tbot(GetFullUserRequest(int(user_id))))
        except Exception:
            user_name = str(user_id)

    if custom_name is not False:
        user_name = custom_name

    return "<a href=\"tg://user?id={id}\">{name}</a>".format(name=user_name, id=user_id)


def user_admin_dec(func):
    async def wrapped(event, *args, **kwargs):

        if hasattr(event, 'from_id'):
            user_id = event.from_id
        elif hasattr(event, 'from_user'):
            user_id = event.from_user.id

        if await check_group_admin(event, user_id, no_msg=True) is False:
            await event.reply("You should be admin to do it!")
            return
        return await func(event, *args, **kwargs)
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
