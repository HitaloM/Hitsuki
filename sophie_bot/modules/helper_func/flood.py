from sophie_bot import SUDO, redis


async def flood_limit(event, command):
    if event.chat_id:
        chat_id = event.chat_id
    else:
        chat_id = event.from_id

    if event.from_id in SUDO:
        return True

    db_name = 'flood_command_{}_{}'.format(chat_id, command)
    redis.incr(db_name, 1)
    number = int(redis.get(db_name))
    redis.expire(db_name, 60)
    if number > 7:
        return False
        redis.expire(db_name, 120)
    if number > 6:
        return False
        await event.reply('**Flood detected!**\nPlease wait 3 minutes before do this again!')
        redis.expire(db_name, 120)
    else:
        return True

def flood_limit_dec(*args):
    def wrapped(func):
        async def wrapped_1(event, *args):
            status = await flood_limit(event, 'test')
            if status is False:
                return
            return await func(event)
        return wrapped_1
    return wrapped
