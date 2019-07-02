from sophie_bot import SUDO, redis


async def flood_limit(command, chat_id):

    if chat_id in SUDO:
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
        redis.expire(db_name, 120)
    else:
        return True


def flood_limit_dec(cmd):
    def wrapped(func):
        async def wrapped_1(event, *args):
            if hasattr(event, 'from_id'):
                user_id = event.from_id
            elif hasattr(event, 'from_user'):
                user_id = event.from_user.id

            status = await flood_limit(user_id, cmd)
            if status is False:
                return
            return await func(event)
        return wrapped_1
    return wrapped
