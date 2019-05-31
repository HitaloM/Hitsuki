import uuid

from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import ChannelParticipantCreator

from sophie_bot import bot, decorator, mongodb
from sophie_bot.modules.language import get_string, get_strings_dec
from sophie_bot.modules.users import user_link, get_user_and_text


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
async def promote_to_fed(event, strings):
    chat_id = event.chat_id
    user_id = event.from_id
    user, fed_id = await get_user_and_text(event)
    if not fed_id:
        chat_fed = mongodb.fed_groups.find_one({'chat_id': chat_id})
        if not chat_fed:
            await event.reply(strings['chat_not_in_fed'])
            return
        fed = mongodb.fed_list.find_one({'fed_id': chat_fed['fed_id']})
    else:
        fed = mongodb.fed_list.find_one({'fed_id': fed_id.lower()})
        if not fed:
            await event.reply(strings['fed_id_invalid'])
            return
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
