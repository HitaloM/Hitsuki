from sophie_bot import bot
from sophie_bot.modules.language import get_strings_dec

from telethon.tl.functions.channels import GetParticipantRequest

# Help
# change_info = rights.change_info
# post_messages = rights.post_messages
# edit_messages = rights.edit_messages delete_messages = rights.delete_messages
# ban_users = rights.ban_users invite_users = rights.invite_users
# pin_messages = rights.pin_messages
# add_admins = rights.add_admins


async def get_bot_rights(event):
    bot_id = await bot.get_me()
    bot_req = await bot(GetParticipantRequest(channel=event.chat_id, user_id=bot_id))
    if bot_req and bot_req.participant and bot_req.participant.admin_rights:
        return bot_req.participant.admin_rights
    return False


def bot_have_del_msgs_rights(func):
    @get_strings_dec("bot_rights")
    async def wrapper(event, strings, *args, **kwargs):
        bot_r = await get_bot_rights(event)
        if bot_r.delete_messages:
            return await func(event, *args, **kwargs)
        else:
            await event.reply(strings["not_right_del_msg"])
    return wrapper
