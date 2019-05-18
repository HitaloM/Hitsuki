from sophie_bot.modules.users import check_group_admin


def is_user_admin(func):
    async def wrapped(event):
        if await check_group_admin(event, event.from_id) is False:
            await event.reply("You should be admin to do it!")
            return
        return await func(event)
    return wrapped
