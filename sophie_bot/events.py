from telethon import events
from sophie_bot import bot, redis


def register(**args):
    pattern = args.get('pattern', None)

    if pattern is not None and not pattern.startswith('(?i)'):
        args['pattern'] = '(?i)' + pattern

    def decorator(func):
        bot.add_event_handler(func, events.NewMessage(**args))
        bot.add_event_handler(func, events.MessageEdited(**args))
        return func

    return decorator


def flood_limit(chat_id, command):
    db_name = 'flood_command_{}_{}'.format(chat_id, command)
    redis.incr(db_name, 1)
    number = int(redis.get(db_name))
    print(number)
    redis.expire(db_name, 60)
    if number > 7:
        return 'EXIT'
        redis.expire(db_name, 120)
    if number > 6:
        return True
        redis.expire(db_name, 120)
    else:
        return False
