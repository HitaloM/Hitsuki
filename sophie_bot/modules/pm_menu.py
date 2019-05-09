from sophie_bot import bot
from sophie_bot.events import register
from sophie_bot.modules.language import lang_info

from telethon import events
from telethon.tl.custom import Button


@register(incoming=True, pattern="^[/!]start$")
async def start(event):
    if not event.chat_id == event.from_id:
        return

    await get_start(event)


@bot.on(events.CallbackQuery(data='start'))
async def start_callback(event):
    await get_start(event)


async def get_start(event):
    text = "Hi i'm SophieBot, i can help you with control your groups."
    keyboard = [[Button.inline("Control panel", 'control_panel')]]
    keyboard += [[
        Button.inline("Language", 'set_lang'),
        Button.inline("Help", 'get_help')
    ]]
    try:
        await event.edit(text, buttons=keyboard)
    except Exception:
        await event.reply(text, buttons=keyboard)


@bot.on(events.CallbackQuery(data='set_lang'))
async def set_lang_callback(event):
    text, buttons = lang_info(event.chat_id, pm=True)
    buttons.append([
        Button.inline("Back", 'start')
    ])
    try:
        await event.edit(text, buttons=buttons)
    except Exception:
        await event.reply(text, buttons=buttons)
