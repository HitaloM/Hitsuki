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

import io
import random
import re
from contextlib import suppress
from datetime import datetime

from aiogram.dispatcher.filters.builtin import CommandStart
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.callback_data import CallbackData
from aiogram.utils.exceptions import MessageToDeleteNotFound, MessageCantBeDeleted
from aiogram.types.inline_keyboard import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types.input_media import InputMediaPhoto
from apscheduler.jobstores.base import JobLookupError
from captcha.image import ImageCaptcha
from telethon.tl.custom import Button

from sophie_bot import BOT_USERNAME, BOT_ID, bot
from sophie_bot.config import get_str_key
from sophie_bot.decorator import register
from sophie_bot.services.apscheduller import scheduler
from sophie_bot.services.mongo import db
from sophie_bot.services.redis import redis
from sophie_bot.services.telethon import tbot
from sophie_bot.stuff.fonts import ALL_FONTS
from .utils.connections import chat_connection
from .utils.language import get_strings_dec
from .utils.message import need_args_dec, convert_time
from .utils.notes import get_parsed_note_list, t_unparse_note_item, send_note
from .utils.restrictions import ban_user
from .utils.restrictions import mute_user, restrict_user, unmute_user, kick_user
from .utils.user_details import is_user_admin, get_user_link, check_admin_rights


class WelcomeSecurityState(StatesGroup):
    button = State()
    captcha = State()
    math = State()


@register(cmds='welcome')
@chat_connection(only_groups=True)
@get_strings_dec('greetings')
async def welcome(message, chat, strings):
    chat_id = chat['chat_id']
    send_id = message.chat.id

    if len(args := message.get_args().split()) > 0:
        no_format = True if 'no_format' == args[0] or 'raw' == args[0] else False
    else:
        no_format = None

    if not (db_item := await db.greetings.find_one({'chat_id': chat_id})):
        db_item = {}
    if 'note' not in db_item:
        db_item['note'] = {'text': strings['default_welcome']}

    if no_format:
        await message.reply(strings['raw_wlcm_note'])
        text, kwargs = await t_unparse_note_item(message, db_item['note'], chat_id, noformat=True)
        await send_note(send_id, text, **kwargs)
        return

    text = strings['welcome_info']

    text = text.format(
        chat_name=chat['chat_title'],
        welcomes_status=strings['disabled'] if 'welcome_disabled' in db_item and db_item[
            'welcome_disabled'] is True else strings['enabled'],
        wlcm_security=strings['disabled']
        if 'welcome_security' not in db_item or db_item['welcome_security']['enabled'] is False
        else strings['wlcm_security_enabled'].format(level=db_item['welcome_security']['level']),
        wlcm_mutes=strings['disabled']
        if 'welcome_mute' not in db_item or db_item['welcome_mute']['enabled'] is False
        else strings['wlcm_mutes_enabled'].format(time=db_item['welcome_mute']['time']),
        clean_welcomes=strings['enabled'] if 'clean_welcome' in db_item and db_item['clean_welcome'][
            'enabled'] is True else strings['disabled'],
        clean_service=strings['enabled'] if 'clean_service' in db_item and db_item['clean_service'][
            'enabled'] is True else strings['disabled'],
    )
    if 'welcome_disabled' not in db_item:
        text += strings['wlcm_note']
        await message.reply(text)
        text, kwargs = await t_unparse_note_item(message, db_item['note'], chat_id)
        await send_note(send_id, text, **kwargs)
    else:
        await message.reply(text)

    if 'welcome_security' in db_item:
        if 'security_note' not in db_item:
            db_item['security_note'] = {'text': strings['default_security_note']}
        await message.reply(strings['security_note'])
        text, kwargs = await t_unparse_note_item(message, db_item['security_note'], chat_id)
        await send_note(send_id, text, **kwargs)


@register(cmds=['setwelcome', 'savewelcome'], user_admin=True)
@chat_connection(admin=True, only_groups=True)
@get_strings_dec('greetings')
async def set_welcome(message, chat, strings):
    chat_id = chat['chat_id']

    if len(args := message.get_args().lower().split()) < 1:
        db_item = await db.greetings.find_one({'chat_id': chat_id})

        if db_item and 'welcome_disabled' in db_item and db_item['welcome_disabled'] is True:
            status = strings['disabled']
        else:
            status = strings['enabled']

        await message.reply(strings['turnwelcome_status'].format(status=status, chat_name=chat['chat_title']))
        return

    no = ['no', 'off', '0', 'false', 'disable']

    if args[0] in no:
        await db.greetings.update_one({'chat_id': chat_id}, {'$set': {'chat_id': chat_id, 'welcome_disabled': True}},
                                      upsert=True)
        await message.reply(strings['turnwelcome_disabled'] % chat['chat_title'])
        return
    else:
        note = await get_parsed_note_list(message, split_args=-1)

        if (await db.greetings.update_one(
                {'chat_id': chat_id},
                {'$set': {'chat_id': chat_id, 'note': note}, '$unset': {'welcome_disabled': 1}},
                upsert=True
        )).modified_count > 0:
            text = strings['updated']
        else:
            text = strings['saved']

        await message.reply(text % chat['chat_title'])


@register(cmds='resetwelcome', user_admin=True)
@chat_connection(admin=True, only_groups=True)
@get_strings_dec('greetings')
async def reset_welcome(message, chat, strings):
    chat_id = chat['chat_id']

    if (await db.greetings.delete_one({'chat_id': chat_id})).deleted_count < 1:
        await message.reply(strings['not_found'])
        return

    await message.reply(strings['deleted'].format(chat=chat['chat_title']))


@register(cmds='cleanwelcome', user_admin=True)
@chat_connection(admin=True, only_groups=True)
@get_strings_dec('greetings')
async def clean_welcome(message, chat, strings):
    chat_id = chat['chat_id']

    if len(args := message.get_args().lower().split()) < 1:
        db_item = await db.greetings.find_one({'chat_id': chat_id})

        if db_item and 'clean_welcome' in db_item and db_item['clean_welcome']['enabled'] is True:
            status = strings['enabled']
        else:
            status = strings['disabled']

        await message.reply(strings['cleanwelcome_status'].format(status=status, chat_name=chat['chat_title']))
        return

    yes = ['yes', 'on', '1', 'true', 'enable']
    no = ['no', 'off', '0', 'false', 'disable']

    if args[0] in yes:
        await db.greetings.update_one(
            {'chat_id': chat_id},
            {'$set': {'chat_id': chat_id, 'clean_welcome': {'enabled': True}}},
            upsert=True
        )
        await message.reply(strings['cleanwelcome_enabled'] % chat['chat_title'])
    elif args[0] in no:
        await db.greetings.update_one({'chat_id': chat_id}, {'$unset': {'clean_welcome': 1}}, upsert=True)
        await message.reply(strings['cleanwelcome_disabled'] % chat['chat_title'])
    else:
        await message.reply(strings['bool_invalid_arg'])


@register(cmds='cleanservice', user_admin=True)
@chat_connection(admin=True, only_groups=True)
@get_strings_dec('greetings')
async def clean_service(message, chat, strings):
    chat_id = chat['chat_id']

    if len(args := message.get_args().lower().split()) < 1:
        db_item = await db.greetings.find_one({'chat_id': chat_id})

        if db_item and 'clean_service' in db_item and db_item['clean_service']['enabled'] is True:
            status = strings['enabled']
        else:
            status = strings['disabled']

        await message.reply(strings['cleanservice_status'].format(status=status, chat_name=chat['chat_title']))
        return

    yes = ['yes', 'on', '1', 'true', 'enable']
    no = ['no', 'off', '0', 'false', 'disable']

    if args[0] in yes:
        await db.greetings.update_one(
            {'chat_id': chat_id},
            {'$set': {'chat_id': chat_id, 'clean_service': {'enabled': True}}},
            upsert=True
        )
        await message.reply(strings['cleanservice_enabled'] % chat['chat_title'])
    elif args[0] in no:
        await db.greetings.update_one({'chat_id': chat_id}, {'$unset': {'clean_service': 1}}, upsert=True)
        await message.reply(strings['cleanservice_disabled'] % chat['chat_title'])
    else:
        await message.reply(strings['bool_invalid_arg'])


@register(cmds='welcomemute', user_admin=True)
@chat_connection(admin=True, only_groups=True)
@get_strings_dec('greetings')
async def welcome_mute(message, chat, strings):
    chat_id = chat['chat_id']

    if len(args := message.get_args().lower().split()) < 1:
        db_item = await db.greetings.find_one({'chat_id': chat_id})

        if db_item and 'welcome_mute' in db_item and db_item['welcome_mute']['enabled'] is True:
            status = strings['enabled']
        else:
            status = strings['disabled']

        await message.reply(strings['welcomemute_status'].format(status=status, chat_name=chat['chat_title']))
        return

    no = ['no', 'off', '0', 'false', 'disable']

    if args[0].endswith(('m', 'h', 'd')):
        await db.greetings.update_one(
            {'chat_id': chat_id},
            {'$set': {'chat_id': chat_id, 'welcome_mute': {'enabled': True, 'time': args[0]}}},
            upsert=True
        )
        await message.reply(strings['welcomemute_enabled'] % chat['chat_title'])
    elif args[0] in no:
        await db.greetings.update_one({'chat_id': chat_id}, {'$unset': {'welcome_mute': 1}}, upsert=True)
        await message.reply(strings['welcomemute_disabled'] % chat['chat_title'])
    else:
        await message.reply(strings['welcomemute_invalid_arg'])


# Welcome Security


@register(cmds='welcomesecurity', user_admin=True)
@chat_connection(admin=True, only_groups=True)
@get_strings_dec('greetings')
async def welcome_security(message, chat, strings):
    chat_id = chat['chat_id']

    if len(args := message.get_args().lower().split()) < 1:
        db_item = await db.greetings.find_one({'chat_id': chat_id})

        if db_item and 'welcome_security' in db_item and db_item['welcome_security']['enabled'] is True:
            status = strings['welcomesecurity_enabled_word'].format(level=db_item['welcome_security']['level'])
        else:
            status = strings['disabled']

        await message.reply(strings['welcomesecurity_status'].format(status=status, chat_name=chat['chat_title']))
        return

    no = ['no', 'off', '0', 'false', 'disable']

    if args[0].lower() in ['button', 'math', 'captcha']:
        level = args[0].lower()
    elif args[0] in no:
        await db.greetings.update_one({'chat_id': chat_id}, {'$unset': {'welcome_security': 1}}, upsert=True)
        await message.reply(strings['welcomesecurity_disabled'] % chat['chat_title'])
        return
    else:
        await message.reply(strings['welcomesecurity_invalid_arg'])
        return

    await db.greetings.update_one(
        {'chat_id': chat_id},
        {'$set': {'chat_id': chat_id, 'welcome_security': {'enabled': True, 'level': level}}},
        upsert=True
    )
    await message.reply(strings['welcomesecurity_enabled'].format(chat_name=chat['chat_title'], level=level))


@register(cmds=['setsecuritynote', 'sevesecuritynote'], user_admin=True)
@need_args_dec()
@chat_connection(admin=True, only_groups=True)
@get_strings_dec('greetings')
async def set_security_note(message, chat, strings):
    chat_id = chat['chat_id']

    if message.get_args().lower().split()[0] in ['raw', 'noformat']:
        db_item = await db.greetings.find_one({'chat_id': chat_id})
        if 'security_note' not in db_item:
            db_item = {'security_note': {}}
            db_item['security_note']['text'] = strings['default_security_note']
            db_item['security_note']['parse_mode'] = 'md'

        text, kwargs = await t_unparse_note_item(message, db_item['security_note'], chat_id, noformat=True)
        kwargs['reply_to'] = message.message_id

        await send_note(chat_id, text, **kwargs)
        return

    note = await get_parsed_note_list(message, split_args=-1)

    if (await db.greetings.update_one({'chat_id': chat_id}, {'$set': {'chat_id': chat_id, 'security_note': note}},
                                      upsert=True)).modified_count > 0:
        text = strings['security_note_updated']
    else:
        text = strings['security_note_saved']

    await message.reply(text % chat['chat_title'])


@register(cmds='delsecuritynote', user_admin=True)
@chat_connection(admin=True, only_groups=True)
@get_strings_dec('greetings')
async def reset_security_note(message, chat, strings):
    chat_id = chat['chat_id']

    if (await db.greetings.update_one({'chat_id': chat_id}, {'$unset': {'security_note': 1}},
                                      upsert=True)).modified_count > 0:
        text = strings['security_note_updated']
    else:
        text = strings['del_security_note_ok']

    await message.reply(text % chat['chat_title'])


@register(only_groups=True, f='welcome')
@get_strings_dec('greetings')
async def welcome_security_handler(message, strings):
    user_id = int(str([user.id for user in message.new_chat_members])[1:-1])
    chat_id = message.chat.id

    if user_id == BOT_ID:
        return

    db_item = await db.greetings.find_one({'chat_id': chat_id})
    if not db_item or 'welcome_security' not in db_item:
        return

    if not await check_admin_rights(chat_id, BOT_ID, ['can_restrict_members']):
        await message.reply(strings['not_admin_ws'])
        return

    user = await message.chat.get_member(user_id)

    # Check if user was muted before
    if 'can_send_messages' in user and user['can_send_messages'] is False:
        return

    # Check on OPs and chat owner
    if await is_user_admin(chat_id, user_id):
        return

    # Mute user
    await mute_user(chat_id, user_id)

    if 'security_note' not in db_item:
        db_item = {'security_note': {}}
        db_item['security_note']['text'] = strings['default_security_note']
        db_item['security_note']['parse_mode'] = 'md'

    text, kwargs = await t_unparse_note_item(message, db_item['security_note'], chat_id)

    db_item = await db.greetings.find_one({'chat_id': chat_id})
    kwargs['reply_to'] = (None if 'clean_service' in db_item and db_item['clean_service']['enabled'] is True
                          else message.message_id)

    kwargs['buttons'] = None if not kwargs['buttons'] else kwargs['buttons']
    msg = await send_note(chat_id, text, **kwargs)

    # Edit msg to apply button
    kwargs['buttons'] = [] if not kwargs['buttons'] else kwargs['buttons']
    kwargs['buttons'] += [Button.url(
        strings['click_here'],
        f'https://t.me/{BOT_USERNAME}?start=ws_{chat_id}_{user_id}_{msg.id}'
    )]

    del kwargs['reply_to']
    await msg.edit(text, **kwargs)

    redis.set(f'welcome_security_users:{user_id}', chat_id)

    scheduler.add_job(
        join_expired,
        "date",
        id=f"wc_expire:{chat_id}:{user_id}",
        run_date=datetime.utcnow() + convert_time(get_str_key('JOIN_CONFIRM_DURATION')),
        kwargs={'chat_id': chat_id, 'user_id': user_id, 'message_id': msg.id, 'wlkm_msg_id': message.message_id},
        replace_existing=True
    )


async def join_expired(chat_id, user_id, message_id, wlkm_msg_id):
    user = await bot.get_chat_member(chat_id, user_id)
    if 'can_send_messages' not in user or user['can_send_messages'] is True:
        return

    bot_user = await bot.get_chat_member(chat_id, BOT_ID)
    if 'can_restrict_members' not in bot_user or bot_user['can_restrict_members'] is False:
        return

    key = 'leave_silent:' + str(chat_id)
    redis.set(key, user_id)

    await unmute_user(chat_id, user_id)
    await kick_user(chat_id, user_id)
    await tbot.delete_messages(chat_id, [message_id, wlkm_msg_id])


@register(CommandStart(re.compile(r'ws_')), allow_kwargs=True)
@get_strings_dec('greetings')
async def welcome_security_handler_pm(message, strings, regexp=None, state=None, **kwargs):
    args = message.get_args().split('_')
    chat_id = int(args[1])
    user_id = message.from_user.id

    async with state.proxy() as data:
        data['chat_id'] = chat_id
        data['msg_id'] = int(args[3])

    if not message.from_user.id == int(args[2]):
        if not (rkey := redis.get(f'welcome_security_users:{user_id}')) and not chat_id == rkey:
            await message.reply(strings['not_allowed'])  # TODO
            return

    db_item = await db.greetings.find_one({'chat_id': chat_id})

    level = db_item['welcome_security']['level']

    if level == 'button':
        await WelcomeSecurityState.button.set()
        await send_button(message, state)

    elif level == 'math':
        await WelcomeSecurityState.math.set()
        await send_btn_math(message, state)

    elif level == 'captcha':
        await WelcomeSecurityState.captcha.set()
        await send_captcha(message, state)


@get_strings_dec('greetings')
async def send_button(message, state, strings):
    text = strings['btn_button_text']
    buttons = InlineKeyboardMarkup().add(InlineKeyboardButton(
        strings['click_here'],
        callback_data='wc_button_btn'
    ))
    verify_msg_id = (await message.reply(text, reply_markup=buttons)).message_id
    async with state.proxy() as data:
        data['verify_msg_id'] = verify_msg_id


@register(regexp='wc_button_btn', f='cb', state=WelcomeSecurityState.button, allow_kwargs=True)
async def wc_button_btn_cb(event, state=None, **kwargs):
    await welcome_security_passed(event, state)


def generate_captcha(number=None):
    if not number:
        number = str(random.randint(10001, 99999))
    captcha = ImageCaptcha(fonts=ALL_FONTS, width=200, height=100).generate_image(number)
    img = io.BytesIO()
    captcha.save(img, 'PNG')
    img.seek(0)
    return img, number


@get_strings_dec('greetings')
async def send_captcha(message, state, strings):
    img, num = generate_captcha()
    async with state.proxy() as data:
        data['captcha_num'] = num
    text = strings['ws_captcha_text'].format(user=await get_user_link(message.from_user.id))

    buttons = InlineKeyboardMarkup().add(InlineKeyboardButton(
        strings['regen_captcha_btn'],
        callback_data='regen_captcha'
    ))

    verify_msg_id = (await message.answer_photo(img, caption=text, reply_markup=buttons)).message_id
    async with state.proxy() as data:
        data['verify_msg_id'] = verify_msg_id


@register(regexp='regen_captcha', f='cb', state=WelcomeSecurityState.captcha, allow_kwargs=True)
@get_strings_dec('greetings')
async def change_captcha(event, strings, state=None, **kwargs):
    message = event.message
    async with state.proxy() as data:
        data['regen_num'] = 1 if 'regen_num' not in data else data['regen_num'] + 1
        regen_num = data['regen_num']

        if regen_num > 3:
            img, num = generate_captcha(number=data['captcha_num'])
            text = strings['last_chance']
            await message.edit_media(InputMediaPhoto(img, caption=text))
            return

        img, num = generate_captcha()
        data['captcha_num'] = num

    text = strings['ws_captcha_text'].format(user=await get_user_link(event.from_user.id))

    buttons = InlineKeyboardMarkup().add(InlineKeyboardButton(
        strings['regen_captcha_btn'],
        callback_data='regen_captcha'
    ))

    await message.edit_media(InputMediaPhoto(img, caption=text), reply_markup=buttons)


@register(f='text', state=WelcomeSecurityState.captcha, allow_kwargs=True)
@get_strings_dec('greetings')
async def check_captcha_text(message, strings, state=None, **kwargs):
    num = message.text.split(' ')[0]

    if not num.isdigit():
        await message.reply(strings['num_is_not_digit'])
        return

    async with state.proxy() as data:
        captcha_num = data['captcha_num']

    if not int(num) == int(captcha_num):
        await message.reply(strings['bad_num'])
        return

    await welcome_security_passed(message, state)


# Btns


def gen_expression():
    a = random.randint(1, 10)
    b = random.randint(1, 10)
    if random.getrandbits(1):
        while a < b:
            b = random.randint(1, 10)
        answr = a - b
        expr = f'{a} - {b}'
    else:
        b = random.randint(1, 10)

        answr = a + b
        expr = f'{a} + {b}'

    return expr, answr


def gen_int_btns(answer):
    buttons = []

    for a in [random.randint(1, 20) for _ in range(3)]:
        while a == answer:
            a = random.randint(1, 20)
        buttons.append(Button.inline(str(a), data='wc_int_btn:' + str(a)))

    buttons.insert(random.randint(0, 3), Button.inline(str(answer), data='wc_int_btn:' + str(answer)))

    return buttons


@get_strings_dec('greetings')
async def send_btn_math(message, state, strings, msg_id=False):
    chat_id = message.chat.id
    expr, answer = gen_expression()

    async with state.proxy() as data:
        data['num'] = answer

    btns = gen_int_btns(answer)

    if msg_id:
        async with state.proxy() as data:
            data['last'] = True
        text = strings['math_wc_rtr_text'] + strings['btn_wc_text'] % expr
    else:
        text = strings['btn_wc_text'] % expr
        msg_id = (await message.reply(text)).message_id

    async with state.proxy() as data:
        data['verify_msg_id'] = msg_id

    await tbot.edit_message(chat_id, msg_id, text, buttons=btns)  # TODO: change to aiogram


@register(regexp='wc_int_btn:', f='cb', state=WelcomeSecurityState.math, allow_kwargs=True)
@get_strings_dec('greetings')
async def wc_math_check_cb(event, strings, state=None, **kwargs):
    num = int(event.data.split(':')[1])

    async with state.proxy() as data:
        answer = data['num']
        if 'last' in data:
            await state.finish()
            await event.answer(strings['math_wc_sry'], show_alert=True)
            await event.message.delete()
            return

    if not num == answer:
        await send_btn_math(event.message, state, msg_id=event.message.message_id)
        await event.answer(strings['math_wc_wrong'], show_alert=True)
        return

    await welcome_security_passed(event, state)


@get_strings_dec('greetings')
async def welcome_security_passed(message, state, strings):
    user_id = message.from_user.id
    async with state.proxy() as data:
        chat_id = data['chat_id']
        msg_id = data['msg_id']
        verify_msg_id = data['verify_msg_id']

    await unmute_user(chat_id, user_id)
    with suppress(MessageToDeleteNotFound, MessageCantBeDeleted):
        await bot.delete_message(chat_id, msg_id)
        await bot.delete_message(user_id, verify_msg_id)
    await state.finish()

    with suppress(JobLookupError):
        scheduler.remove_job(f"wc_expire:{chat_id}:{user_id}")

    title = (await db.chat_list.find_one({'chat_id': chat_id}))['chat_title']

    if 'data' in message:
        await message.answer(strings['passed_no_frm'] % title, show_alert=True)
    else:
        await message.reply(strings['passed'] % title)

    db_item = await db.greetings.find_one({'chat_id': chat_id})

    if 'message' in message:
        message = message.message

    # Welcome
    if 'note' in db_item:
        text, kwargs = await t_unparse_note_item(
            message.reply_to_message,
            db_item['note'],
            chat_id
        )
        await send_note(user_id, text, **kwargs)

    # Welcome mute
    if 'welcome_mute' in db_item and db_item['welcome_mute']['enabled'] is not False:
        user = await bot.get_chat_member(chat_id, user_id)
        if 'can_send_messages' not in user or user['can_send_messages'] is True:
            await restrict_user(chat_id, user_id, until_date=convert_time(db_item['welcome_mute']['time']))


# End Welcome Security

# Welcomes
@register(only_groups=True, f='welcome')
@get_strings_dec('greetings')
async def welcome_trigger(message, strings):
    chat_id = message.chat.id
    user_id = int(str([user.id for user in message.new_chat_members])[1:-1])

    if user_id == BOT_ID:
        return

    if not (db_item := await db.greetings.find_one({'chat_id': chat_id})):
        db_item = {}

    if 'welcome_disabled' in db_item and db_item['welcome_disabled'] is True:
        return

    if 'welcome_security' in db_item and db_item['welcome_security']['enabled']:
        return

    # Welcome
    if 'note' not in db_item:
        db_item['note'] = {
            'text': strings['default_welcome'],
            'parse_mode': 'md'
        }
    reply_to = (message.message_id if 'clean_welcome' in db_item and db_item['clean_welcome']['enabled'] is not False
                else None)
    text, kwargs = await t_unparse_note_item(message, db_item['note'], chat_id)
    msg = await send_note(chat_id, text, reply_to=reply_to, **kwargs)
    # Clean welcome
    if 'clean_welcome' in db_item and db_item['clean_welcome']['enabled'] is not False:
        if 'last_msg' in db_item['clean_welcome']:
            with suppress(MessageToDeleteNotFound, MessageCantBeDeleted):
                await bot.delete_message(chat_id, db_item['clean_welcome']['last_msg'])
        await db.greetings.update_one({'_id': db_item['_id']}, {'$set': {'clean_welcome.last_msg': msg.id}},
                                      upsert=True)

    # Welcome mute
    if user_id == BOT_ID:
        return
    if 'welcome_mute' in db_item and db_item['welcome_mute']['enabled'] is not False:
        user = await bot.get_chat_member(chat_id, user_id)
        if 'can_send_messages' not in user or user['can_send_messages'] is True:
            if not await check_admin_rights(chat_id, BOT_ID, ['can_restrict_members']):
                await message.reply(strings['not_admin_wm'])
                return

            await restrict_user(chat_id, user_id, until_date=convert_time(db_item['welcome_mute']['time']))


# Clean service trigger
@register(only_groups=True, f='service')
@get_strings_dec('greetings')
async def clean_service_trigger(message, strings):
    chat_id = message.chat.id

    if message.new_chat_members[0].id == BOT_ID:
        return

    if not (db_item := await db.greetings.find_one({'chat_id': chat_id})):
        return

    if 'clean_service' not in db_item or db_item['clean_service']['enabled'] is False:
        return

    if not await check_admin_rights(chat_id, BOT_ID, ['can_delete_messages']):
        await bot.send_message(chat_id, strings['not_admin_wsr'])
        return

    with suppress(MessageToDeleteNotFound, MessageCantBeDeleted):
        await message.delete()

# WelcomeRestrict
whitelist_cb = CallbackData('whitelist_cb', 'chat_id', 'user_id')
ban_cb = CallbackData('ban_cb', 'chat_id', 'user_id')


@register(cmds='welcomerestrict', is_admin=True, bot_can_restrict_members=True, bot_can_delete_messages=True)
@chat_connection(admin=True)
@get_strings_dec('greetings')
async def welcomerestrict_cmd(message, chat, strings):
    chat_id = chat['chat_id']
    disable = ['no', 'off', '0', 'false', 'disable']
    enable = ['yes', 'on', '1', 'true', 'enable']

    database = await db.greetings.find_one({'chat_id': chat_id})
    if len(args := message.get_args().split()) < 1:
        if database is not None and 'welcome_restrict' in database and database['welcome_restrict']['enabled'] is True:
            state = strings['enabled']
        else:
            state = strings['disabled']
        await message.reply(strings['restrict_status'].format(state=state, chat=chat['chat_title']))
    else:
        if args[0] in disable:
            if database is not None:
                if 'welcome_restrict' not in database or database['welcome_restrict']['enabled'] is False:
                    return await message.reply(strings['already_disabled'])
            await db.greetings.update_one(
                {'chat_id': chat_id},
                {'$unset': {'welcome_restrict': 1}},
                upsert=True
            )
            await message.reply(strings['disabled_sucessfully'].format(chat=chat['chat_title']))
        elif args[0] in enable:
            if database is not None:
                if 'welcome_restrict' in database and database['welcome_restrict']['enabled'] is True:
                    await message.reply(strings['already_enabled'])
            else:
                await db.greetings.update_one(
                    {'chat_id': chat_id},
                    {'$set': {'chat_id': chat_id, 'welcome_restrict': {'enabled': True}}},
                    upsert=True
                )
                await message.reply(strings['enabled_sucessfully'].format(chat=chat['chat_title']))
        else:
            return await message.reply(strings['unkown_option'])


@register(f='welcome')
async def welcome_restrict(message):
    chat_id = message.chat.id
    user_id = message.new_chat_members[0].id
    if not await is_user_admin(chat_id, user_id):
        redis.set(f'new_chatmember:{chat_id}:{user_id}', 1, ex=86400)


@register(f='any', only_groups=True)
async def welcomerestrict_handler(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    database = await db.greetings.find_one({'chat_id': chat_id})
    if not database:
        return

    if 'welcome_restrict' in database and database['welcome_restrict']['enabled'] is True:
        if not await is_user_admin(chat_id, user_id):
            if await new_joinee(user_id, chat_id):
                if await check_forward(message):
                    return await restrict_action(message, 'fwd')
                if 'url' in [entities.type for entities in message.entities]:
                    return await restrict_action(message, 'url')
                if await check_media(message):
                    return await restrict_action(message, 'media')


@get_strings_dec('greetings')
async def restrict_action(message, item, strings=None):
    chat_id = message.chat.id
    user_id = message.from_user.id

    buttons = InlineKeyboardMarkup()
    buttons.add(InlineKeyboardButton(strings['whitelist'],
                                     callback_data=whitelist_cb.new(chat_id=chat_id, user_id=user_id)))
    buttons.add(InlineKeyboardButton(strings['ban'],
                                     callback_data=ban_cb.new(chat_id=chat_id, user_id=user_id)))
    await message.delete()
    await message.answer(strings[f'del_{item}'].format(user=await get_user_link(user_id)), reply_markup=buttons)


@register(ban_cb.filter(), f='cb', user_can_restrict_members=True, bot_can_restrict_members=True, allow_kwargs=True)
@get_strings_dec('greetings')
async def ban_button_cb(messsage, strings, callback_data=None, **kwargs):
    chat_id = callback_data['chat_id']
    user_id = callback_data['user_id']
    from_user = messsage.from_user.id

    if await ban_user(chat_id, user_id):
        await messsage.message.edit_text(strings['banned'].format(
            user=await get_user_link(user_id),
            by=await get_user_link(from_user)
        ))


@register(whitelist_cb.filter(), f='cb', allow_kwargs=True, is_admin=True)
@get_strings_dec('greetings')
async def whitlist_btn_cb(message, strings, callback_data=None, **kwargs):
    chat_id = callback_data['chat_id']
    user_id = callback_data['user_id']
    from_user = message.from_user.id

    redis.delete(f'new_chatmember:{chat_id}:{user_id}')
    await message.message.edit_text(strings['whitelisted'].format(
        user=await get_user_link(user_id),
        by=await get_user_link(from_user)
    ))


async def new_joinee(user_id, chat_id):
    if redis.exists(f'new_chatmember:{chat_id}:{user_id}'):
        return True


async def check_media(message):
    media_types = ['audio', 'document', 'photo', 'sticker', 'video', 'video_note', 'voice']
    for media in media_types:
        if media not in message:
            continue
        return True
    return False


async def check_forward(message):
    forwards = ['forward_from', 'forward_from_chat']
    for forward in forwards:
        if forward not in message:
            continue
        return True
    return False


async def __export__(chat_id):
    if greetings := await db.greetings.find_one({'chat_id': chat_id}):
        del greetings['_id']
        del greetings['chat_id']

        return {'greetings': greetings}


async def __import__(chat_id, data):
    await db.greetings.update_one({'chat_id': chat_id}, {'$set': data}, upsert=True)
