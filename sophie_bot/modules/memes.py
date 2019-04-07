import asyncio
import random

from sophie_bot.events import flood_limit, register
from sophie_bot.modules.language import get_string


@register(incoming=True, pattern="^/runs$")
async def event(event):

    res = flood_limit(event.chat_id, 'runs1')
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

    res = False #flood_limit(event.chat_id, 'insults')
    if res == 'EXIT':
        return
    elif res is True:
        await event.reply('**Flood detected! **\
Please wait 3 minutes before using this command')
        return

    await event.reply(
        random.choice(
            get_string('INSULTS', event.chat_id)))
