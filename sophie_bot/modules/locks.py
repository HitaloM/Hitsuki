from sophie_bot.modules.connections import connection
from sophie_bot.modules.users import is_user_admin
from sophie_bot import decorator, bot, mongodb, redis


ALLOWED_LOCKS = (
    'all',
    'text',
)


# Locks processor
@decorator.AioBotDo()
async def locks_processor(message):
    # Get locks
    chat_id = message.chat.id

    if await is_user_admin(chat_id, message.from_user.id):
        return

    key = 'locks_cache_{}'.format(chat_id)
    locks = None
    if redis.llen(key) == 0:
        return
    if redis.exists(key) > 0:
        locks = redis.lrange(key, 0, -1)
    if not locks:
        update_locks_cache(chat_id)
        locks = redis.lrange(key, 0, -1)
    locks = [x.decode('utf-8') for x in locks]

    if 'all' in locks:
        await message.delete()

def update_locks_cache(chat_id):
    key = 'locks_cache_{}'.format(chat_id)
    redis.delete(key)
    data = mongodb.locks.find_one({'chat_id': chat_id})
    for lock in data:
        if lock == 'chat_id' or lock == '_id':
            continue
        if data[lock] is True:
            redis.lpush(key, lock)
    redis.expire(key, 3600)


@decorator.command('locktypes')
async def locktypes_list(message):
    text = "<b>Lock-able items are:</b>\n"
    for item in ALLOWED_LOCKS:
        text += f'* <code>{item}</code>\n'

    await message.reply(text)


@decorator.command('lock')
@connection(admin=True, only_in_groups=True)
async def lock(message, status, chat_id, chat_title):
    item = message.get_args().lower()
    if item not in ALLOWED_LOCKS:
        await message.reply('You cant lock this!')
        return

    mongodb.locks.update_one({'chat_id': chat_id}, {"$set": {item: True}}, upsert=True)
    update_locks_cache(chat_id)
    await message.reply(f'Locked <code>{item}</code> in <b>{chat_title}</b>!')


@decorator.command('unlock')
@connection(admin=True, only_in_groups=True)
async def unlock(message, status, chat_id, chat_title):
    item = message.get_args().lower()
    if item not in ALLOWED_LOCKS:
        await message.reply('You cant unlock this!')
        return

    mongodb.locks.update_one({'chat_id': chat_id}, {"$set": {item: False}}, upsert=True)
    update_locks_cache(chat_id)
    await message.reply(f'Unlocked <code>{item}</code> in <b>{chat_title}</b>!')
