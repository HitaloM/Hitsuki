# This file is part of Hitsuki (Telegram Bot)

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

from contextlib import suppress

from aiogram.types.inline_keyboard import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.utils.exceptions import MessageNotModified

from hitsuki.decorator import register
from hitsuki.modules.utils.disable import disableable_dec
from .language import select_lang_keyboard
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
    buttons.add(InlineKeyboardButton(strings['btn_channel'], url='https://t.me/HitsukiNews'),
                InlineKeyboardButton(strings['btn_source'], url='https://github.com/HitsukiNetwork/HitsukiX'))
    # Handle error when user click the button 2 or more times simultaneously
    with suppress(MessageNotModified):
        await task(strings['start_hi'], reply_markup=buttons)


@register(regexp='get_help', f='cb')
@get_strings_dec('pm_menu')
async def help_cb(event, strings):
    button = InlineKeyboardMarkup()
    button.add(InlineKeyboardButton(text='AntiFlood', url='https://telegra.ph/Hitsuki-AntiFlood-Help-12-07'),
               InlineKeyboardButton(
                   text='Connections', url='https://telegra.ph/Hitsuki-Connections-Help-12-07'),
               InlineKeyboardButton(text='Disabling', url='https://telegra.ph/Hitsuki-Disabling-Help-12-08'))
    button.add(InlineKeyboardButton(text='Federations', url='https://telegra.ph/Hitsuki-Federations-Help-12-08'),
               InlineKeyboardButton(
                   text='Filters', url='https://telegra.ph/Hitsuki-Filters-Help-12-08'),
               InlineKeyboardButton(text='Greetings', url='https://telegra.ph/Hitsuki-Greetings-Help-12-08'))
    button.add(InlineKeyboardButton(text='Backups', url='https://telegra.ph/Hitsuki-Backups-Help-12-08'),
               InlineKeyboardButton(
                   text='Language', url='https://telegra.ph/Hitsuki-Language-Help-12-08'),
               InlineKeyboardButton(text='Locks', url='https://telegra.ph/Hitsuki-Locks-Help-12-08'))
    button.add(InlineKeyboardButton(text='Misc', url='https://telegra.ph/Hitsuki-Misc-Help-12-08'),
               InlineKeyboardButton(
                   text='Notes', url='https://telegra.ph/Hitsuki-Notes-Help-12-08'),
               InlineKeyboardButton(text='Admin', url='https://telegra.ph/Hitsuki-Admin-Help-12-08'))
    button.add(InlineKeyboardButton(text='Reporting', url='https://telegra.ph/Hitsuki-Reporting-Help-12-08'),
               InlineKeyboardButton(
                   text='Restrictions', url='https://telegra.ph/Hitsuki-Restrictions-Help-12-08'),
               InlineKeyboardButton(text='Rules', url='https://telegra.ph/Hitsuki-Rules-Help-12-08'))
    button.add(InlineKeyboardButton(text='Stickers',
                                    url='https://telegra.ph/Hitsuki-Stickers-Help-12-08'),
               InlineKeyboardButton(text='Anime',
                                    url='https://telegra.ph/Hitsuki-Anime-Help-12-08'),
               InlineKeyboardButton(text='Android',
                                    url='https://telegra.ph/Hitsuki-Android-Help-12-08'))
    button.add(InlineKeyboardButton(
        strings['back'], callback_data='go_to_start'))
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
        strings['btn_help'], url='https://t.me/Hitsuki_BOT?start'
    ))
    await message.reply(strings['help_headerg'], reply_markup=button)
