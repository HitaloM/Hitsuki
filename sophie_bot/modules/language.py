# Copyright (C) 2018 - 2020 MrYacha. All rights reserved. Source code available under the AGPL.
# Copyright (C) 2019 Aiogram

#
# This file is part of SophieBot.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from aiogram.types.inline_keyboard import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

from sophie_bot.decorator import register
from sophie_bot.services.mongo import db
from sophie_bot.services.quart import quart
from .utils.api import html_white_text
from .utils.language import LANGUAGES, get_strings_dec, change_chat_lang, get_chat_lang_info, get_strings
from .utils.message import get_arg

select_lang_cb = CallbackData('select_lang_cb', 'lang')
translators_lang_cb = CallbackData('translators_lang_cb', 'lang')


@register(cmds='lang', no_args=True, user_can_change_info=True)
@get_strings_dec('language')
async def select_lang_keyboard(message, strings):
    markup = InlineKeyboardMarkup(row_width=2)

    lang_info = await get_chat_lang_info(message.chat.id)

    if message.chat.type == 'private':
        text = strings['your_lang'].format(
            lang=lang_info['flag'] + " " + lang_info['babel'].display_name)
        text += strings['select_pm_lang']

    # TODO: Connected chat lang info

    else:
        text = strings['chat_lang'].format(
            lang=lang_info['flag'] + " " + lang_info['babel'].display_name)
        text += strings['select_chat_lang']

    for lang in LANGUAGES.values():
        lang_info = lang['language_info']
        markup.insert(InlineKeyboardButton(
            lang_info['flag'] + " " + lang_info['babel'].display_name,
            callback_data=select_lang_cb.new(lang=lang_info['code']))
        )

    markup.add(InlineKeyboardButton(strings['crowdin_btn'], url='https://crowdin.com/project/sophiebot'))

    await message.reply(text, reply_markup=markup)


async def change_lang(message, lang, e=False):
    chat_id = message.chat.id
    await change_chat_lang(chat_id, lang)

    strings = await get_strings(chat_id, 'language')

    lang_info = LANGUAGES[lang]['language_info']

    text = strings['lang_changed'].format(lang_name=lang_info['flag'] + " " + lang_info['babel'].display_name)
    text += strings['help_us_translate']

    markup = InlineKeyboardMarkup()

    if 'translators' in lang_info:
        markup.add(InlineKeyboardButton(strings['see_translators'], callback_data=translators_lang_cb.new(lang=lang)))

    if e:
        await message.edit_text(text, reply_markup=markup, disable_web_page_preview=True)
    else:
        await message.reply(text, reply_markup=markup, disable_web_page_preview=True)


@register(cmds='lang', has_args=True, user_can_change_info=True)
@get_strings_dec('language')
async def select_lang_msg(message, strings):
    lang = get_arg(message).lower()

    if lang not in LANGUAGES:
        await message.reply(strings['not_supported_lang'])
        return

    await change_lang(message, lang)


@register(select_lang_cb.filter(), f='cb', allow_kwargs=True, )
async def select_lang_callback(query, callback_data=None, **kwargs):
    lang = callback_data['lang']
    await change_lang(query.message, lang, e=True)


@quart.route('/wiki/languages_loaded')
async def languages_loaded_wiki_page():
    text = "<h2>Loaded languages:</h2>"

    text += '<ul>'
    for language in LANGUAGES.values():
        info = language['language_info']
        text += f"\n<li>{info['flag']} {info['babel'].display_name}</li>"

    text += '</ul>'

    return html_white_text(text)


async def __stats__():
    return f"* <code>{len(LANGUAGES)}</code> languages loaded.\n"


async def __export__(chat_id):
    lang = await get_chat_lang_info(chat_id)

    return {'language': lang['code']}


async def __import__(chat_id, data):
    if data not in LANGUAGES:
        return
    await db.lang.update_one({'chat_id': chat_id}, {"$set": {'lang': data}}, upsert=True)
