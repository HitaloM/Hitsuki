import re
import asyncio
import random

from sophie_bot import MONGO
from sophie_bot.events import flood_limit, register
from sophie_bot.modules.language import get_string


@register(incoming=True, pattern="^/runs$")
async def event(event):
    if is_memes_enabled(event.chat_id) is False:
        return

    res = flood_limit(event.chat_id, 'runs')
    if res == 'EXIT':
        return
    elif res is True:
        await event.reply('**Flood detected! **\
Please wait 3 minutes before using this command')
        return

    await event.reply(
        random.choice(
            get_string('RUNS', event.chat_id)))


@register(incoming=True, pattern="^/insults$")
async def event(event):
    if is_memes_enabled(event.chat_id) is False:
        return

    res = flood_limit(event.chat_id, 'insults')
    if res == 'EXIT':
        return
    elif res is True:
        await event.reply('**Flood detected! **\
Please wait 3 minutes before using this command')
        return

    await event.reply(
        random.choice(
            get_string('INSULTS', event.chat_id)))


@register(incoming=True, pattern=r"^/memes ?(.*)$")
async def event(event):
    arg = event.pattern_match.group(1)
    chat_id = event.chat_id
    if "yes" in arg or "1" in arg:
        old = MONGO.memes_enabled.find_one({'chat_id': chat_id})
        if old:
            MONGO.memes_enabled.delete_one({'_id': old['_id']})
        MONGO.memes_enabled.insert_one({'chat_id': chat_id})
        await event.reply('Memes enabled for this chat!')
    elif "no" in arg or "0" in arg:
        old = MONGO.memes_enabled.find_one({'chat_id': chat_id})
        if old:
            MONGO.memes_enabled.delete_one({'_id': old['_id']})
        await event.reply('Memes disabled for this chat!')
    else:
        await event.reply('I don\'t understand what you wanna from me')


def is_memes_enabled(chat_id):
    lol = MONGO.memes_enabled.find_one({'chat_id': chat_id})
    if lol:
        return True
    else:
        return False
