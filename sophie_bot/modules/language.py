import re
from telethon.tl.custom import Button
from telethon import events

from sophie_bot.events import register, flood_limit
from sophie_bot.modules.users import is_user_admin
from sophie_bot import REDIS, MONGO, bot

from sophie_bot.modules.lang import EN_STRINGS, RU_STRINGS

SUPPORTED_LANGUAGES = {
    'en': 'English 🇺🇸',
    'ru': 'Russian 🇷🇺',
}

LANG_VARS = {
    'en': EN_STRINGS,
    'ru': RU_STRINGS,
}


@register(incoming=True, pattern="^/lang$")
async def handler(event):
    res = flood_limit(event.chat_id, 'lang')
    if res == 'EXIT':
        return
    elif res is True:
        await event.reply('**Flood detected! **\
Please wait 3 minutes before using this command')
        return

    if event.chat_id == event.from_id:
        pm = True
    else:
        pm = False

    K = await is_user_admin(event.chat_id, event.from_id)
    if K is False:
        await event.reply("You don't have rights to set language here!")
        return

    text, buttons = lang_info(event.chat_id, pm=pm)
    await event.reply(text, buttons=buttons)


@bot.on(events.CallbackQuery(data=re.compile(b'select_lang_')))
async def event(event):
    chat = event.chat_id
    event_data = re.search(r'select_lang_(.*)', str(event.data))
    lang = event_data.group(1)[:-1]
    REDIS.set('lang_cache_{}'.format(chat), lang)
    MONGO.lang.insert_one({'chat_id': chat, 'lang': lang})
    await event.edit(
        "Language changed to **{}**!".format(SUPPORTED_LANGUAGES[lang]))


def get_string(text, chat_id):
    lang = get_chat_lang(chat_id)
    for H in LANG_VARS:
        if H == lang and text in LANG_VARS[H]:
            return LANG_VARS[H][text]

    return text


def get_chat_lang(chat_id):
    r = REDIS.get('lang_cache_{}'.format(chat_id))
    if r:
        return r.decode('utf-8')
    else:
        db_lang = MONGO.lang.find_one({'chat_id': chat_id})
        if db_lang:
            # Rebuild lang cache
            REDIS.set('lang_cache_{}'.format(chat_id), db_lang['lang'])
            return db_lang['lang']
        user_lang = MONGO.user_list.find_one({'user_id': chat_id})
        if user_lang and user_lang['user_lang'] in SUPPORTED_LANGUAGES:
            # Add telegram language in lang cache
            REDIS.set('lang_cache_{}'.format(chat_id), user_lang['user_lang'])
            return user_lang['user_lang']
        else:
            return 'en'


def lang_info(chat_id, pm=False):
    text = "**Select language**\n"
    locale = get_chat_lang(chat_id)
    if locale and pm is False:
        text += "Current chat locale - `{}`".format(locale)
    elif locale and pm is True:
        text += "Your locale - `{}`".format(locale)
    buttons = []
    for a in SUPPORTED_LANGUAGES:
        buttons.append(
            [Button.inline(SUPPORTED_LANGUAGES[a],
             'select_lang_{}'.format(a))])
    return text, buttons
