import re

from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import MessageEntityMentionName

from sophie_bot import decorator, mongodb
from sophie_bot.modules.disable import disablable_dec
from sophie_bot.modules.helper_func.flood import t_flood_limit_dec
from sophie_bot.modules.users import user_link


@decorator.command("afk ?(.*)", arg=True)
@disablable_dec("afk")
@t_flood_limit_dec("afk")
async def afk(event):
    if not event.pattern_match.group(1):
        reason = "No reason"
    else:
        reason = event.pattern_match.group(1)
    mongodb.afk.insert_one({'user': event.from_id, 'reason': reason})
    text = "{} is AFK!".format(await user_link(event.from_id))
    if reason:
        text += "\nReason: " + reason
    await event.reply(text)


async def get_user(event):
    if event.reply_to_msg_id:
        previous_message = await event.get_reply_message()
        replied_user = await event.client(GetFullUserRequest(previous_message.from_id))
    else:
        user = re.search('@(\w*)', event.text)
        if not user:
            return
        user = user.group(0)

        if user.isnumeric():
            user = int(user)

        if not user:
            self_user = await event.client.get_me()
            user = self_user.id

        if event.message.entities is not None:
            probable_user_mention_entity = event.message.entities[0]

            if isinstance(probable_user_mention_entity, MessageEntityMentionName):
                user_id = probable_user_mention_entity.user_id
                replied_user = await event.client(GetFullUserRequest(user_id))
                return replied_user
        try:
            user_object = await event.client.get_entity(user)
            replied_user = await event.client(GetFullUserRequest(user_object.id))
        except (TypeError, ValueError) as err:
            await event.edit(str(err))
            return None

    return replied_user


@decorator.insurgent()
@t_flood_limit_dec("check_afk")
async def check_afk(event):
    user_afk = mongodb.afk.find_one({'user': event.from_id})
    if user_afk:
        rerere = re.findall('[!/]afk(.*)|brb ?(.*)', event.text)
        if not rerere:
            await event.reply("{} is not AFK anymore!".format(await user_link(event.from_id)))
            mongodb.afk.delete_one({'_id': user_afk['_id']})

    user = await get_user(event)
    if not user:
        return
    user_afk = mongodb.afk.find_one({'user': user.user.id})
    if user_afk:
        await event.reply("{} is AFK!\nReason: {}".format(
            await user_link(user.user.id), user_afk['reason']))
