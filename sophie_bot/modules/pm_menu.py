# Copyright (C) 2018 - 2020 MrYacha. All rights reserved. Source code available under the AGPL.
# Copyright (C) 2019 Aiogram
# Copyright (C) 2020 Jeepeo

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

from aiogram.utils.exceptions import MessageNotModified
from aiogram.types.inline_keyboard import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from contextlib import suppress
from .language import select_lang_keyboard

from sophie_bot.decorator import register
from sophie_bot.modules.utils.disable import disableable_dec
from .utils.language import get_strings_dec


@register(cmds='start', no_args=True, only_groups=True)
@disableable_dec('start')
@get_strings_dec('pm_menu')
async def start_group_cmd(message, strings):
    await message.reply(strings['start_hi_group'])


@register(cmds='start', no_args=True, only_pm=True)
async def start_cmd(message):
    await get_start_func(message)


@get_strings_dec('pm_menu')
async def get_start_func(message, strings, edit=False):
    msg = message.message if hasattr(message, 'message') else message
    task = msg.edit_text if edit else msg.reply
    buttons = InlineKeyboardMarkup()
    buttons.add(InlineKeyboardButton(strings['btn_help'], callback_data='get_help'),
                InlineKeyboardButton(strings['btn_lang'], callback_data='lang_btn'))
    buttons.add(InlineKeyboardButton(strings['btn_chat'], url='https://t.me/SophieSupport'),
                InlineKeyboardButton(strings['btn_channel'], url='https://t.me/sophieNEWS'))
    # Handle error when user click the button 2 or more times simultaneously
    with suppress(MessageNotModified):
        await task(strings['start_hi'], reply_markup=buttons)


@register(regexp='get_help', f='cb')
@get_strings_dec('pm_menu')
async def help_cb(event, strings):
    button = InlineKeyboardMarkup()
    button.add(InlineKeyboardButton(strings['click_btn'], url='https://wiki.sophiebot.gq'))
    button.add(InlineKeyboardButton(strings['back'], callback_data='go_to_start'))
    with suppress(MessageNotModified):
        await event.message.edit_text(strings['help_header'], reply_markup=button)


@register(regexp='lang_btn', f='cb')
async def set_lang_cb(event):
    await select_lang_keyboard(event.message, edit=True)


@register(regexp='go_to_start', f='cb')
async def back_btn(event):
    await get_start_func(event, edit=True)


@register(cmds='help')
@disableable_dec('help')
@get_strings_dec('pm_menu')
async def help_cmd(message, strings):
    button = InlineKeyboardMarkup().add(InlineKeyboardButton(
        strings['click_btn'], url='https://wiki.sophiebot.gq'
    ))
    await message.reply(strings['help_header'], reply_markup=button)
