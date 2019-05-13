import re

from sophie_bot import BOT_NICK, bot, logger
from sophie_bot.events import register
from sophie_bot.modules.flood import flood_limit
from sophie_bot.modules.language import LANGUAGES, get_chat_lang, get_string, lang_info

from telethon import custom, events
from telethon.tl.custom import Button


# Genrate help
HELP = []
for module in LANGUAGES['en']['HELPS']:
    HELP.append(module)
HELP = sorted(HELP)
logger.info("Help loaded for: {}".format(HELP))


@register(incoming=True, pattern="^[/!]start ?(@)?(?(1){})$".format(BOT_NICK))
async def start(event):
    if await flood_limit(event, 'start') is False:
        return
    if not event.from_id == event.chat_id:
        await event.reply('Hey there, My name is Sophie!')
        return
    text, buttons = get_start(event)
    await event.reply(text, buttons=buttons)


@bot.on(events.CallbackQuery(data='get_start'))
async def get_start_callback(event):
    text, buttons = get_start(event)
    await event.edit(text, buttons=buttons)


def get_start(event):
    text = "Hey there! My name is Sophie :3, I help you manage your group and more!"
    buttons = [[Button.inline('❔ Help', 'get_help')]]
    buttons += [[Button.inline("🇷🇺 Language", 'set_lang')]]
    buttons += [[custom.Button.url('👥 Group', 'https://t.me/YanaBotGroup'),
                 custom.Button.url('📡 Channel', 'https://t.me/YanaBotNEWS')]]

    return text, buttons


@bot.on(events.CallbackQuery(data='set_lang'))
async def set_lang_callback(event):
    text, buttons = lang_info(event.chat_id, pm=True)
    buttons.append([
        Button.inline("Back", 'get_start')
    ])
    try:
        await event.edit(text, buttons=buttons)
    except Exception:
        await event.reply(text, buttons=buttons)


@bot.on(events.CallbackQuery(data='get_help'))
async def get_help_callback(event):
    text, buttons = get_help(event)
    try:
        await event.edit(text, buttons=buttons)
    except Exception:
        await event.reply(text, buttons=buttons)


def get_help(event):
    text = "Select module to get help"
    chat_id = event.chat_id
    buttons = []
    counter = 0
    for module in HELP:
        counter += 1
        btn_name = get_string(module, "btn", chat_id, dir="HELPS")
        t = [Button.inline(btn_name, 'mod_help_' + module)]
        if counter % 2 == 0:
            new = buttons[-1] + t
            buttons = buttons[:-1]
            buttons.append(new)
        else:
            buttons.append(t)
    return text, buttons


@bot.on(events.CallbackQuery(data=re.compile(r'mod_help_(.*)')))
async def get_mod_help_callback(event):
    chat_id = event.chat_id
    module = re.search('mod_help_(.*)', str(event.data)).group(1)[:-1]
    text = get_string(module, "title", chat_id, dir="HELPS")
    text += '\n'
    lang = get_chat_lang(chat_id)
    for string in get_string(module, "text", chat_id, dir="HELPS"):
        if "HELPS" in LANGUAGES[lang]:
            text += LANGUAGES[lang]["HELPS"][module]['text'][string]
        else:
            text += LANGUAGES["en"]["HELPS"][module]['text'][string]
        text += '\n'
    buttons = [[Button.inline("Back", 'get_help')]]
    await event.edit(text, buttons=buttons)
