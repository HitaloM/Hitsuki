import asyncio
import subprocess
import uuid

from telethon.tl.functions.channels import (EditBannedRequest,
                                            GetParticipantRequest)
from telethon.tl.types import ChannelParticipantCreator, ChatBannedRights

from sophie_bot import WHITELISTED, bot, decorator, mongodb
from sophie_bot.modules.language import get_string, get_strings_dec
from sophie_bot.modules.users import (get_user, get_user_and_text,
                                      is_user_admin, user_link)


def get_user_and_fed_and_text_dec(func):
    async def wrapped_1(event, *args, **kwargs):
        user = await get_user(event)
        # Count of - in group(2) to see if its a fed id
        F = 0
        text = ""
        for a in event.pattern_match.group(2):
            if a == "-":
                F += 1
        if F == 4:  # group(2) is id
            chat_fed = await get_chat_fed(event, event.pattern_match.group(2))
            if chat_fed is False:
                return
        else:
            chat_fed = mongodb.fed_groups.find_one({'chat_id': event.chat_id})
            if not chat_fed:
                await event.reply(get_string("feds", 'chat_not_in_fed', event.chat_id))
                return
            text += event.pattern_match.group(2)
            text += " "
        if event.pattern_match.group(3):
            text += event.pattern_match.group(3)

        fed = mongodb.fed_list.find_one({'fed_id': chat_fed['fed_id']})

        return await func(event, user, fed, text, *args, **kwargs)
    return wrapped_1


def get_user_and_fed_dec(func):
    async def wrapped_1(event, *args, **kwargs):
        chat_id = event.chat_id
        user, fed_id = await get_user_and_text(event)
        if not fed_id:
            chat_fed = mongodb.fed_groups.find_one({'chat_id': chat_id})
            if not chat_fed:
                await event.reply(get_string("feds", 'chat_not_in_fed', chat_id))
                return
            fed = mongodb.fed_list.find_one({'fed_id': chat_fed['fed_id']})
        else:
            fed = mongodb.fed_list.find_one({'fed_id': fed_id.lower()})
            if not fed:
                await event.reply(get_string("feds", 'fed_id_invalid', chat_id))
                return
        return await func(event, user, fed, *args, **kwargs)
    return wrapped_1


def get_chat_fed_dec(func):
    async def wrapped_1(event, *args, **kwargs):
        fed_id = event.pattern_match.group(1)
        fed = await get_chat_fed(event, fed_id)
        if fed is False:
            return
        return await func(event, fed, *args, **kwargs)
    return wrapped_1


async def get_chat_fed(event, fed_id):
    chat_id = event.chat_id
    if not fed_id:
        chat_fed = mongodb.fed_groups.find_one({'chat_id': chat_id})
        if not chat_fed:
            await event.reply(get_string("feds", 'chat_not_in_fed', event.chat_id))
            return False
        fed = mongodb.fed_list.find_one({'fed_id': chat_fed['fed_id']})
    else:
        fed = mongodb.fed_list.find_one({'fed_id': fed_id})
        if not fed:
            await event.reply(get_string("feds", 'fed_id_invalid', event.chat_id))
            return False
    return fed


def user_is_fed_admin(func):
    async def wrapped_1(event, *args, **kwargs):
        group_fed = mongodb.fed_groups.find_one({'chat_id': event.chat_id})
        if not group_fed:
            await event.reply(get_string("feds", 'chat_not_in_fed', event.chat_id))
            return False
        fed = mongodb.fed_list.find_one({'fed_id': group_fed['fed_id']})
        user_id = event.from_id
        if not user_id == fed['creator']:
            fadmins = mongodb.fed_admins.find({'fed_id': fed['fed_id'], 'admin': user_id})
            if not fadmins:
                await event.reply(get_string("feds", 'need_admin_to_fban', event.chat_id).format(
                    name=fed['fed_name']))
        return await func(event, *args, **kwargs)
    return wrapped_1


@decorator.command('newfed', arg=True)
@get_strings_dec("feds")
async def newFed(event, strings):
    args = event.pattern_match.group(1)
    if not args:
        await event.reply(strings['no_args'])
    fed_name = args
    creator = event.from_id
    fed_id = str(uuid.uuid4())
    data = {'fed_name': fed_name, 'fed_id': fed_id, 'creator': creator}
    check = mongodb.fed_list.insert_one(data)
    if check:
        text = strings['created_fed']
        await event.reply(text.format(name=fed_name, id=fed_id, cr=await user_link(creator)))


@decorator.command('joinfed', arg=True)
@get_strings_dec("feds")
async def join_fed_comm(event, strings):
    fed_id = event.pattern_match.group(1)
    chat = event.chat_id
    user = event.from_id
    if await join_fed(event, chat, fed_id, user) is True:
        fed_name = mongodb.fed_list.find_one({'fed_id': fed_id})['fed_name']
        await event.reply(strings['join_fed_success'].format(name=fed_name))


@decorator.command('leavefed')
@get_strings_dec("feds")
async def leave_fed_comm(event, strings):
    chat = event.chat_id
    user = event.from_id
    if await leave_fed(event, chat, user) is True:
        await event.reply(strings['leave_fed_success'])


@decorator.command('fpromote', arg=True)
@get_strings_dec("feds")
@get_user_and_fed_dec
async def promote_to_fed(event, user, fed, strings):
    user_id = event.from_id

    if not user_id == fed["creator"]:
        await event.reply(strings["only_creator_promote"])
        return
    data = {'fed_id': fed['fed_id'], 'admin': user['user_id']}

    old = mongodb.fed_admins.find_one(data)
    if old:
        await event.reply(strings["admin_already_in_fed"].format(
            user=await user_link(user['user_id']), name=fed['fed_name']))
        return
    mongodb.fed_admins.insert_one(data)
    await event.reply(strings["admin_added_to_fed"].format(
        user=await user_link(user['user_id']), name=fed['fed_name']))


@decorator.command('fchatlist', arg=True)
@get_strings_dec("feds")
@get_chat_fed_dec
async def fed_chat_list(event, fed, strings):
    text = strings['chats_in_fed'].format(name=fed['fed_name'])
    chats = mongodb.fed_groups.find({'fed_id': fed['fed_id']})
    for fed in chats:
        chat = mongodb.chat_list.find_one({'chat_id': fed['chat_id']})
        text += '* {} (`{}`)\n'.format(chat["chat_title"], fed['chat_id'])
    if len(text) > 4096:
        output = open("output.txt", "w+")
        output.write(text)
        output.close()
        await event.client.send_file(
            event.chat_id,
            "output.txt",
            reply_to=event.id,
            caption="`Output too large, sending as file`",
        )
        subprocess.run(["rm", "output.txt"], stdout=subprocess.PIPE)
        return
    await event.reply(text)


@decorator.command('finfo', arg=True)
@get_strings_dec("feds")
@get_chat_fed_dec
async def fed_info(event, fed, strings):
    text = strings['fed_info']
    text += strings['fed_name'].format(name=fed['fed_name'])
    text += strings['fed_id'].format(id=fed['fed_id'])
    text += strings['fed_creator'].format(user=await user_link(fed['creator']))
    chats = mongodb.fed_groups.find({'fed_id': fed['fed_id']})
    text += strings['chats_in_fed_info'].format(num=chats.count())
    await event.reply(text)


@decorator.command('fban', word_arg=True, additional=" ?(\S*) ?(.*)")
@get_strings_dec("feds")
@get_user_and_fed_and_text_dec
@user_is_fed_admin
async def fban_user(event, user, fed, reason, strings):

    if event.from_id == 172811422:
        return

    if reason == " ":
        reason = 'No reason'

    if int(user['user_id']) in WHITELISTED:
        await event.reply(strings['user_wl'])
        return

    bot_id = await bot.get_me()
    bot_id = bot_id.id
    if user['user_id'] == bot_id:
        await event.reply(strings['fban_self'])
        return

    check = mongodb.fbanned_users.find_one({'user': user['user_id'], 'fed_id': fed['fed_id']})
    if check:
        await event.reply(strings['already_fbanned'].format(
                          user=await user_link(user['user_id'])))
        return

    fed_name = mongodb.fed_list.find_one({'fed_id': fed['fed_id']})['fed_name']
    text = strings['fban_success_reply'].format(user=await user_link(user['user_id']),
                                                fadmin=await user_link(event.from_id),
                                                fed=fed_name,
                                                rsn=reason)
    try:
        banned_rights = ChatBannedRights(
            until_date=None,
            view_messages=True,
            send_messages=True,
            send_media=True,
            send_stickers=True,
            send_gifs=True,
            send_games=True,
            send_inline=True,
            embed_links=True,
        )

        await event.client(
            EditBannedRequest(
                event.chat_id,
                user['user_id'],
                banned_rights
            )
        )
    except Exception:
        pass

    mongodb.fbanned_users.insert_one({'user': user['user_id'], 'fed_id': fed['fed_id'],
                                      'reason': reason})
    await event.reply(text)  # TODO(Notify all fedadmins)


@decorator.command('unfban', word_arg=True, additional=" ?(\S*) ?(.*)")
@get_strings_dec("feds")
@get_user_and_fed_and_text_dec
@user_is_fed_admin
async def unfban_user(event, user, fed, reason, strings):
    from_id = event.from_id

    bot_id = await bot.get_me()
    bot_id = bot_id.id
    if user == bot_id:
        await event.reply(strings['unfban_self'])
        return

    check = mongodb.fbanned_users.find_one({'user': user['user_id'], 'fed_id': fed['fed_id']})
    if not check:
        await event.reply(strings['user_not_fbanned'].format(
                          user=await user_link(user['user_id'])))
        return

    fed_chats = mongodb.fed_groups.find({'fed_id': fed['fed_id']})

    msg = await event.reply(strings["unfban_started"].format(
        user=await user_link(user['user_id']),
        fed_name=fed["fed_name"],
        admin=await user_link(from_id)
    ))

    for chat in fed_chats:
        await asyncio.sleep(1)  # Do not slow down other updates
        try:
            unbanned_rights = ChatBannedRights(
                until_date=None,
                view_messages=False,
                send_messages=False,
                send_media=False,
                send_stickers=False,
                send_gifs=False,
                send_games=False,
                send_inline=False,
                embed_links=False,
            )

            await event.client(
                EditBannedRequest(
                    chat['chat_id'],
                    user['user_id'],
                    unbanned_rights
                )
            )
        except Exception as err:
            await msg.edit(err)

    mongodb.fbanned_users.delete_one({'_id': check['_id']})

    await msg.edit(strings["unfban_completed"].format(
        user=await user_link(user['user_id']),
        fed_name=fed["fed_name"],
        admin=await user_link(from_id)
    ))


@decorator.command('subfed', arg=True)
@get_strings_dec('feds')
async def subfed(event, strings):
    chat = event.chat_id

    chat_fed = mongodb.fed_groups.find_one({'chat_id': chat})
    if not chat_fed:  # find chatfed
        await event.reply(strings['no_fed_2'])
        return

    fed_id = chat_fed['fed_id']
    user = event.from_id
    creator = mongodb.fed_list.find_one({'fed_id': fed_id})
    creator = creator['creator']
    if int(user) != int(creator):  # only fed creator can subscribe
        await event.reply(strings['only_creator'])
        return

    if not event.pattern_match.group(1):  # check if fed id given
        await event.reply(strings['no_arg_given'])
        return

    subfed_id = event.pattern_match.group(1)  # get details of subscribing fed id and check fed id
    check1 = mongodb.fed_list.find_one({'fed_id': subfed_id})
    if not check1:
        await event.reply(strings['invalid_fedid'])
        return

    data = {'fed_id': fed_id, 'subfed_id': subfed_id}
    check = mongodb.subfed_list.find_one(data)
    if check:
        await event.reply(strings['already_subfed'])
        return

    fedname = check1['fed_name']
    await event.reply(strings['subfed_success'].format(fedname=fedname))
    mongodb.subfed_list.insert_one(data)


@decorator.command('unsubfed', arg=True)
@get_strings_dec('feds')
async def unsubfed(event, strings):
    chat = event.chat_id

    chatfed = mongodb.fed_groups.find_one({'chat_id': chat})
    if not chatfed:
        await event.reply(strings['no_fed_3'])
        return

    fed_id = chatfed['fed_id']
    user = event.from_id
    creator = mongodb.fed_list.find_one({'fed_id': fed_id})
    creator = creator['creator']
    if int(user) != int(creator):
        await event.reply(strings['only_creator_2'])
        return

    if not event.pattern_match.group(1):
        await event.reply(strings['no_arg_given_2'])
        return

    subfed = event.pattern_match.group(1)
    data = {'fed_id': fed_id, 'subfed_id': subfed}
    check = mongodb.subfed_list.find_one(data)
    if not check:
        await event.reply(strings["fed_n'tsubscribed"])
        return

    check = mongodb.fed_list.find_one({'fed_id': fed_id})
    fedname = check['fed_name']
    await event.reply(strings['unsub_success'].format(fedname=fedname))
    mongodb.subfed_list.delete_one(data)


@decorator.command('fedsubs')
@get_strings_dec('feds')
@user_is_fed_admin
async def subfedlist(event, strings):
    chat = event.chat_id

    chatfed = mongodb.fed_groups.find_one({'chat_id': chat})
    if not chatfed:
        await event.reply(strings['no_fed_4'])
        return

    fed_id = chatfed['fed_id']
    subfeds = mongodb.subfed_list.find({'fed_id': fed_id})
    if subfeds.count() == 0:
        await event.reply(strings['no_subfeds'])
        return

    for subfed in subfeds:
        fed_details = mongodb.fed_list.find_one({'fed_id': subfed['subfed_id']})
        fedname = fed_details['fed_name']

        text = strings['list_head']
        text += strings['list_data'].format(fedname=fedname)

        await event.reply(text)


async def join_fed(event, chat_id, fed_id, user):
    peep = await bot(
        GetParticipantRequest(
            channel=chat_id, user_id=user,
        )
    )
    if not peep.participant == ChannelParticipantCreator(user_id=user):
        await event.reply(get_string('feds', 'only_creators', chat_id))
        return

    check = mongodb.fed_list.find_one({'fed_id': fed_id})
    if check is False:  # Assume Fed ID invalid
        await event.reply(get_string('feds', 'fed_id_invalid', chat_id))
        return

    old = mongodb.fed_groups.find_one({'chat_id': chat_id})
    if old:  # Assume chat already joined this/other fed
        await event.reply(get_string('feds', 'joined_fed_already', chat_id))
        return

    join_data = {'chat_id': chat_id, 'fed_id': fed_id}
    mongodb.fed_groups.insert_one(join_data)

    return True


async def leave_fed(event, chat_id, user):
    peep = await bot(
        GetParticipantRequest(
            channel=chat_id, user_id=user,
        )
    )
    if not peep.participant == ChannelParticipantCreator(user_id=user):
        await event.reply(get_string('feds', 'only_creators', chat_id))
        return

    old = mongodb.fed_groups.delete_one({'chat_id': chat_id}).deleted_count
    if old < 1:  # If chat not was in any federation
        await event.reply(get_string('feds', 'chat_not_in_fed', chat_id))
        return

    return True


@decorator.insurgent()
@get_strings_dec('feds')
async def fban_helper(event, strings):
    user = event.from_id
    chat = event.chat_id

    chat_fed = mongodb.fed_groups.find_one({'chat_id': chat})
    if not chat_fed:
        return

    if await is_user_admin(chat, user) is True:
        return

    if str(user) in WHITELISTED:
        return

    fed_id = chat_fed['fed_id']
    fed_name = mongodb.fed_list.find_one({'fed_id': fed_id})
    if not fed_name:
        return
    fed_name = fed_name['fed_name']

    is_banned = mongodb.fbanned_users.find_one({'user': user, 'fed_id': fed_id})
    if not is_banned:
        return

    banned_rights = ChatBannedRights(
        until_date=None,
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
        ban = await event.client(
            EditBannedRequest(
                chat,
                user,
                banned_rights
            )
        )

        if ban:
            await event.respond(strings['fban_usr_rmvd'].format(fed=fed_name,
                                                                user=await user_link(user),
                                                                rsn=is_banned['reason']))

    except Exception:
        pass


@decorator.ChatAction()
@get_strings_dec('feds')
async def fban_helper_2(event, strings):
    if event.user_joined is True or event.user_added is True:
        if hasattr(event.action_message.action, 'users'):
            from_id = event.action_message.action.users[0]
        else:
            from_id = event.action_message.from_id
    else:
        return  # ?

    chat = event.chat_id

    chat_fed = mongodb.fed_groups.find_one({'chat_id': chat})
    if not chat_fed:
        return

    if await is_user_admin(chat, from_id) is True:
        return

    if str(from_id) in WHITELISTED:
        return

    fed_id = chat_fed['fed_id']
    fed_name = mongodb.fed_list.find_one({'fed_id': fed_id})
    if not fed_name:
        return
    fed_name = fed_name['fed_name']

    is_banned = mongodb.fbanned_users.find_one({'user': from_id, 'fed_id': fed_id})
    if not is_banned:
        return

    banned_rights = ChatBannedRights(
        until_date=None,
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
        ban = await event.client(
            EditBannedRequest(
                chat,
                from_id,
                banned_rights
            )
        )

        if ban:
            await event.respond(strings['fban_usr_rmvd'].format(fed=fed_name,
                                                                user=await user_link(from_id),
                                                                rsn=is_banned['reason']))

    except Exception:
        pass
