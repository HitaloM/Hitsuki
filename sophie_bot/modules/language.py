# Copyright (C) 2019 The Raphielscape Company LLC.
# Copyright (C) 2018 - 2019 MrYacha
#
# This file is part of SophieBot.
#
# SophieBot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.

import os
import re
import yaml

from telethon.tl.custom import Button

from sophie_bot import decorator, logger, mongodb, redis
from sophie_bot.modules.users import is_user_admin, user_link

LANGUAGES = {}
LANGS = []

# logger.debug("Loading English localisation..")
# f = open('sophie_bot/modules/langs/en.yaml', "r")
# lang = yaml.load(f, Loader=yaml.CLoader)
# LANGUAGES[lang['language_info']['code']] = lang
# LANGS.append(lang['language_info']['code'])

for filename in os.listdir('sophie_bot/modules/langs'):
    logger.debug("Loading language file " + filename)
    f = open('sophie_bot/modules/langs/' + filename, "r")
    lang = yaml.load(f, Loader=yaml.CLoader)

    lang_code = lang['language_info']['code']
    LANGS.append(lang_code)
    LANGUAGES[lang_code] = lang


LANGS.sort()

logger.info("Languages loaded: {}".format(LANGS))


@decorator.t_command("lang")
async def lang(event):
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


@decorator.t_command("lang", arg=True)
async def lang_with_arg(event):
    if not event.pattern_match.group(1):
        return

    arg = event.pattern_match.group(1).lower()

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

    text = "Language changed to **{}**".format(arg)

    if 'translators' in LANGUAGES[arg]["language_info"]:
        text += "\n\n**Translators:**\n"
        for user in LANGUAGES[arg]["language_info"]['translators']:
            text += "• "
            text += await user_link(user)
            text += '\n'

    await event.reply(text)


@decorator.CallBackQuery(b'select_lang_')
async def set_lang_callback(event):
    chat = event.chat_id
    K = await is_user_admin(chat, event.original_update.user_id)
    if K is False:
        await event.answer("You don't have rights to set language here!", alert=True)
        return
    event_data = re.search(r'select_lang_(.*)', event.data.decode("utf-8"))
    lang = event_data.group(1)
    redis.set('lang_cache_{}'.format(chat), lang)
    old = mongodb.lang.find_one({'chat_id': chat})
    if old:
        mongodb.notes.delete_one({'_id': old['_id']})
    mongodb.lang.insert_one({'chat_id': chat, 'lang': lang})
    text = "Language changed to **{}**!".format(
        LANGUAGES[lang]["language_info"]["name"] + " " + LANGUAGES[lang]["language_info"]["flag"])
    if 'translators' in LANGUAGES[lang]["language_info"]:
        text += "\n\n**Translators:**\n"
        for user in LANGUAGES[lang]["language_info"]['translators']:
            text += "• "
            text += await user_link(user)
            text += '\n'
    await event.edit(text)


def get_string(module, text, chat_id, dir="STRINGS"):
    lang = get_chat_lang(chat_id)

    if dir in LANGUAGES[lang] and \
        module in LANGUAGES[lang][dir] and \
            text in LANGUAGES[lang][dir][module]:
        return LANGUAGES[lang][dir][module][text]

    if text in LANGUAGES['en'][dir][module]:
        return LANGUAGES['en'][dir][module][text]
    return text


def get_chat_lang(chat_id):
    r = redis.get('lang_cache_{}'.format(chat_id))
    if r:
        return r
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
        lang_name = LANGUAGES[lang]["language_info"]["name"]
        lang_flag = LANGUAGES[lang]["language_info"]["flag"]
        lang_code = LANGUAGES[lang]["language_info"]["code"]
        buttons.append(
            [Button.inline(lang_name + " " + lang_flag,
             'select_lang_{}'.format(lang_code))])
    return text, buttons


def get_strings(chat_id, module="", mas_name="STRINGS"):
    chat_lang = get_chat_lang(chat_id)
    if chat_lang not in LANGUAGES:
        return False  # TODO: Change lang to en

    str = LANGUAGES[chat_lang][mas_name][module]
    return str


def get_strings_dec(module="", mas_name="STRINGS"):
    def wrapped(func):
        async def wrapped_1(event, *args, **kwargs):
            if hasattr(event, 'chat_id'):
                chat_id = event.chat_id
            elif hasattr(event, 'chat'):
                chat_id = event.chat.id
            elif hasattr(event, 'message'):
                chat_id = event.message.chat.id

            str = get_strings(chat_id, module=module, mas_name=mas_name)
            return await func(event, str, *args, **kwargs)
        return wrapped_1
    return wrapped
