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

from aiogram.utils.callback_data import CallbackData
from aiogram.utils.exceptions import MessageNotModified
from aiogram.types.inline_keyboard import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.utils.exceptions import MessageNotModified

from hitsuki.decorator import register
from hitsuki.modules.utils.disable import disableable_dec
from . import MOD_HELP
from .utils.disable import disableable_dec
from .utils.language import get_strings_dec
from .language import select_lang_keyboard

helpmenu_cb = CallbackData('helpmenu', 'mod')


def help_markup(modules):
    markup = InlineKeyboardMarkup()
    for module in modules:
        markup.insert(InlineKeyboardButton(module, callback_data=helpmenu_cb.new(mod = module)))
    return markup


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
    button = help_markup(MOD_HELP)
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
    button = help_markup(MOD_HELP)
    await message.reply(strings['help_header'], reply_markup=button)


@register(helpmenu_cb.filter(), f='cb', allow_kwargs=True)
async def helpmenu_callback(query, callback_data=None, **kwargs):
    mod = callback_data['mod']
    if not mod in MOD_HELP:
        await query.answer()
        return
    msg = f"Help for <b>{mod} module</b>\n"
    msg += f"{MOD_HELP[mod]}"
    with suppress(MessageNotModified):
        await query.message.edit_text(msg, disable_web_page_preview=True)
        await query.answer('Help for ' + mod)
