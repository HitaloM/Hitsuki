import subprocess
import uuid

from telethon.tl.functions.channels import (EditBannedRequest,
                                            GetParticipantRequest)
from telethon.tl.types import ChannelParticipantCreator, ChatBannedRights

from sophie_bot import bot, decorator, mongodb
from sophie_bot.modules.language import get_string, get_strings_dec
from sophie_bot.modules.users import get_user, get_user_and_text, user_link


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
            print('ogogo')
            fed = await get_chat_fed(event, event.pattern_match.group(2))
            if fed is False:
                return
        else:
            print('owowo')
            fed = mongodb.fed_groups.find_one({'chat_id': event.chat_id})
            if not fed:
                await event.reply(get_string("feds", 'chat_not_in_fed', event.chat_id))
                return
            text += event.pattern_match.group(2)
            text += " "
        if event.pattern_match.group(3):
            text += event.pattern_match.group(3)

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
    print(fed_id)
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
    bot_id = await bot.get_me()
    if user == bot_id:
        await event.reply(strings['fban_self'])

    check = mongodb.fbanned_users.find_one({'user': user['user_id'], 'fed_id': fed['fed_id']})
    if check:
        await event.reply(strings['already_fbanned'].format(
                          user=await user_link(user['user_id'])))
        return
    mongodb.fbanned_users.insert_one({'user': user['user_id'], 'fed_id': fed['fed_id']})

    chats = mongodb.fed_groups.find({'fed_id': fed['fed_id']})
    if chats:
        for chat in chats:
            try:
                await event.client(
                    EditBannedRequest(
                        chat['chat_id'],
                        user['user_id'],
                        banned_rights
                    )
                )
            except Exception:
                pass


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
