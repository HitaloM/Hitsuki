import os
import re

from sophie_bot import bot, logger, mongodb, redis
from sophie_bot.events import flood_limit, register
from sophie_bot.modules.users import is_user_admin

from telethon import events
from telethon.tl.custom import Button

import ujson


LANGUAGES = {}
LANGS = ()

for filename in os.listdir('sophie_bot/modules/langs'):
    f = open('sophie_bot/modules/langs/' + filename, "r")
    lang = ujson.load(f)
    exec("LANGUAGES[\"" + lang['language_info']['code'] + "\"] = lang")
    LANGS += tuple([lang['language_info']['code']])

logger.info("Languages loaded: {}".format(LANGS))


@register(incoming=True, pattern="^[/!]lang$")
async def lang(event):
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


@register(incoming=True, pattern="^[/!]lang (.*)$")
async def lang_with_arg(event):
    res = flood_limit(event.chat_id, 'lang')
    if res == 'EXIT':
        return
    elif res is True:
        await event.reply('**Flood detected! **\
Please wait 3 minutes before using this command')
        return

    arg = event.message.raw_text.split(" ", 2)[1]

    K = await is_user_admin(event.chat_id, event.from_id)
    if K is False:
        await event.reply("You don't have rights to set language here!")
        return

    if arg not in LANGS:
        await event.reply("I don't support this language yet!")
        return

    old = mongodb.lang.find_one({'chat_id': event.chat_id})
    if old:
        mongodb.notes.delete_one({'_id': old['_id']})

    mongodb.lang.insert_one({'chat_id': event.chat_id, 'lang': arg})
    redis.set('lang_cache_{}'.format(event.chat_id), arg)
    await event.reply("Language changed to {}".format(arg))


@bot.on(events.CallbackQuery(data=re.compile(b'select_lang_')))
async def set_lang_callback(event):
    chat = event.chat_id
    K = await is_user_admin(chat, event.original_update.user_id)
    if K is False:
        await event.answer("You don't have rights to set language here!", alert=True)
        return
    event_data = re.search(r'select_lang_(.*)', str(event.data))
    lang = event_data.group(1)[:-1]
    redis.set('lang_cache_{}'.format(chat), lang)
    old = mongodb.lang.find_one({'chat_id': chat})
    if old:
        mongodb.notes.delete_one({'_id': old['_id']})
    mongodb.lang.insert_one({'chat_id': chat, 'lang': lang})
    await event.edit(
        "Language changed to **{}**!".format(
            LANGUAGES[lang]["language_info"]["name"] + " \
                " + LANGUAGES[lang]["language_info"]["flag"]
        ))


def get_string(module, text, chat_id):
    lang = get_chat_lang(chat_id)

    if module in LANGUAGES[lang]['STRINGS'] and \
            text in LANGUAGES[lang]['STRINGS'][module]:
        return LANGUAGES[lang]['STRINGS'][module][text]

    if text in LANGUAGES['en']['STRINGS'][module]:
        return LANGUAGES['en']['STRINGS'][module][text]
    return text


def get_chat_lang(chat_id):
    r = redis.get('lang_cache_{}'.format(chat_id))
    if r:
        return r.decode('utf-8')
    else:
        db_lang = mongodb.lang.find_one({'chat_id': chat_id})
        if db_lang:
            # Rebuild lang cache
            redis.set('lang_cache_{}'.format(chat_id), db_lang['lang'])
            return db_lang['lang']
        user_lang = mongodb.user_list.find_one({'user_id': chat_id})
        if user_lang and user_lang['user_lang'] in LANGS:
            # Add telegram language in lang cache
            redis.set('lang_cache_{}'.format(chat_id), user_lang['user_lang'])
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
    for lang in LANGS:
        print(lang)
        lang_name = LANGUAGES[lang]["language_info"]["name"]
        lang_flag = LANGUAGES[lang]["language_info"]["flag"]
        lang_code = LANGUAGES[lang]["language_info"]["code"]
        buttons.append(
            [Button.inline(lang_name + " " + lang_flag,
             'select_lang_{}'.format(lang_code))])
    return text, buttons
