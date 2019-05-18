from sophie_bot import SUDO, OWNER_ID
from sophie_bot.modules.users import check_group_admin


def is_user_admin(func):
    async def wrapped(event):
        if await check_group_admin(event, event.from_id) is False:
            await event.reply("You should be admin to do it!")
            return
        return await func(event)
    return wrapped


def is_user_sudo(func):
    async def wrapped(event):
        if event.from_id not in SUDO:
            return
        return await func(event)
    return wrapped


def is_user_owner(func):
    async def wrapped(event):
        if not event.from_id == OWNER_ID:
            return
        return await func(event)
    return wrapped
