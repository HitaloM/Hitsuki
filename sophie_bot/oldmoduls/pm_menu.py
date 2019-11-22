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

from aiogram.dispatcher.filters.builtin import CommandStart
from aiogram.types.inline_keyboard import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
from sophie_bot.modules.language import (LANGUAGES, get_chat_lang, get_string,
                                         lang_info, get_strings_dec, get_strings)
from telethon.tl.custom import Button

from sophie_bot import BOT_USERNAME, decorator, logger, dp, bot

help_page_cp = CallbackData('help_page', 'module')
help_btn_cp = CallbackData('help_btn', 'module', 'btn')


# Generate help cache
HELP = []
for module in LANGUAGES['en']['HELPS']:
    logger.debug("Loading help for " + module)
    HELP.append(module)
HELP = sorted(HELP)
logger.info("Help loaded for: {}".format(HELP))


@decorator.register(cmds=['start', 'ping'], disable_args=True, only_groups=True)
async def start(event):
    await event.reply('Hey there, My name is Sophie!')
    return


@decorator.register(cmds='start', disable_args=True, only_pm=True)
async def start_pm(message):
    text, buttons = get_start(message.chat.id)
    await message.reply(text, reply_markup=buttons)


@decorator.register(cmds='help', only_groups=True)
@get_strings_dec('misc')
async def help_btn(message, strings):
    buttons = InlineKeyboardMarkup().add(InlineKeyboardButton(
        strings['help_btn'], url=f'https://t.me/{BOT_USERNAME}?start=help'
    ))
    text = strings['help_txt']
    await message.reply(text, reply_markup=buttons)


@decorator.register(cmds='help', only_pm=True)
async def help(message):
    text, buttons = get_help(message.chat.id)
    await message.reply(text, reply_markup=buttons)


@decorator.callback_query_deprecated(b'get_start')
async def get_start_callback(event):
    text, buttons = get_start(event)
    await event.edit(text, reply_markup=buttons)


def get_start(chat_id):
    strings = get_strings(chat_id, module='pm_menu')

    text = strings["start_hi"]
    buttons = InlineKeyboardMarkup()
    buttons.add(InlineKeyboardButton(strings["btn_help"], callback_data='get_help'))
    buttons.add(InlineKeyboardButton(strings["btn_lang"], callback_data='set_lang'))

    buttons.add(
        InlineKeyboardButton(strings["btn_chat"], url='https://t.me/SophieSupport'),
        InlineKeyboardButton(strings["btn_channel"], url='https://t.me/SophieNEWS'),
    )

    return text, buttons


@decorator.callback_query_deprecated(b'set_lang')
async def set_lang_callback(event):
    text, buttons = lang_info(event.chat_id, pm=True)
    buttons.append([
        Button.inline("Back", 'get_start')
    ])
    try:
        await event.edit(text, buttons=buttons)
    except Exception:
        await event.reply(text, buttons=buttons)


@dp.callback_query_handler(regexp='get_help')
async def get_help_callback(query):
    chat_id = query.message.chat.id
    text, buttons = get_help(chat_id)
    await bot.edit_message_text(text, chat_id, query.message.message_id, reply_markup=buttons)


def get_help(chat_id):
    text = "Select module to get help"
    counter = 0
    buttons = InlineKeyboardMarkup(row_width=2)
    for module in HELP:
        counter += 1
        btn_name = get_string(module, "btn", chat_id, dir="HELPS")
        buttons.insert(InlineKeyboardButton(btn_name, callback_data=help_page_cp.new(module=module)))
    return text, buttons


@dp.callback_query_handler(help_page_cp.filter())
async def get_mod_help_callback(query, callback_data=False, **kwargs):
    chat_id = query.message.chat.id
    message = query.message
    module = callback_data['module']
    lang = get_chat_lang(chat_id)
    buttons = InlineKeyboardMarkup(row_width=2)
    text = LANGUAGES[lang]["HELPS"][module]['text']
    if 'buttons' in LANGUAGES[lang]["HELPS"][module]:
        counter = 0
        for btn in LANGUAGES[lang]["HELPS"][module]['buttons']:
            counter += 1
            btn_name = LANGUAGES[lang]["HELPS"][module]['buttons'][btn]
            buttons.insert(InlineKeyboardButton(
                btn_name, callback_data=help_btn_cp.new(module=module, btn=btn)))
    buttons.add(InlineKeyboardButton("Back", callback_data='get_help'))
    await message.edit_text(text, reply_markup=buttons)


@dp.callback_query_handler(help_btn_cp.filter())
async def get_help_button_callback(query, callback_data=False, **kwargs):
    message = query.message
    module = callback_data['module']
    data = callback_data['btn']
    chat_id = query.message.chat.id
    lang = get_chat_lang(chat_id)
    text = ""
    text += LANGUAGES[lang]["HELPS"][module][data]
    buttons = InlineKeyboardMarkup().add(InlineKeyboardButton("Back", callback_data='get_help'))
    await message.edit_text(text, reply_markup=buttons)


@dp.message_handler(CommandStart('help'))
async def help_start(message):
    text, buttons = get_help(message.chat.id)
    await message.answer(text, reply_markup=buttons)
