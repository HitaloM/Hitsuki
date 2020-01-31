# Copyright (C) 2019 The Raphielscape Company LLC.
# Copyright (C) 2018-2019 MrYacha
# Copyright (C) 2017-2019 Aiogram
#
# This file is part of SophieBot.
#
# SophieBot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.

import html
import re
import sys

from aiogram.types.inline_keyboard import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import markdown

from telethon.tl.custom import Button

from .tmarkdown_converter import tbold, titalic, tpre, tcode, tlink
from .user_details import get_user_link

from .message import get_args

from sophie_bot import BOT_USERNAME
from sophie_bot.services.telethon import tbot


BUTTONS = {}

ALLOWED_COLUMNS = [
    'parse_mode',
    'file',
    'text',
    'preview'
]


def tparse_ent(ent, text, as_html=True):
    if not text:
        return text

    etype = ent.type
    offset = ent.offset
    length = ent.length

    if sys.maxunicode == 0xffff:
        return text[offset:offset + length]

    if not isinstance(text, bytes):
        entity_text = text.encode('utf-16-le')
    else:
        entity_text = text

    entity_text = entity_text[offset * 2:(offset + length) * 2].decode('utf-16-le')

    if etype == 'bold':
        method = markdown.hbold if as_html else tbold
        return method(entity_text)
    if etype == 'italic':
        method = markdown.hitalic if as_html else titalic
        return method(entity_text)
    if etype == 'pre':
        method = markdown.hpre if as_html else tpre
        return method(entity_text)
    if etype == 'code':
        method = markdown.hcode if as_html else tcode
        return method(entity_text)
    if etype == 'url':
        return entity_text
    if etype == 'text_link':
        method = markdown.hlink if as_html else tlink
        return method(entity_text, ent.url)
    if etype == 'text_mention' and ent.user:
        return ent.user.get_mention(entity_text, as_html=as_html)

    return entity_text


def get_parsed_msg(message):
    if not message.text:
        return '', 'md'

    text = message.text or message.caption

    mode = get_msg_parse(text)
    if mode == 'html':
        as_html = True
    else:
        as_html = False

    entities = message.entities or message.caption_entities

    if not entities:
        return text, mode

    if not sys.maxunicode == 0xffff:
        text = text.encode('utf-16-le')

    result = ''
    offset = 0

    for entity in sorted(entities, key=lambda item: item.offset):
        entity_text = tparse_ent(entity, text, as_html=as_html)

        if sys.maxunicode == 0xffff:
            part = text[offset:entity.offset]
            result += part + entity_text
        else:
            part = text[offset * 2:entity.offset * 2].decode('utf-16-le')
            result += part + entity_text

        offset = entity.offset + entity.length

    if sys.maxunicode == 0xffff:
        result += text[offset:]
    else:
        result += text[offset * 2:].decode('utf-16-le')

    result = re.sub(r'\[format:(\w+)\]', '', result)
    result = re.sub(r'%PARSEMODE_(\w+)', '', result)

    if not result:
        result = ''

    return result, mode


def get_msg_parse(text, default_md=True):
    if '[format:html]' in text or '%PARSEMODE_HTML' in text:
        return 'html'
    elif '[format:none]' in text or '%PARSEMODE_NONE' in text:
        return 'none'
    elif '[format:md]' in text or '%PARSEMODE_MD' in text:
        return 'md'
    else:
        if not default_md:
            return None
        return 'md'


def parse_button(data, name):
    raw_button = data.split('_')
    raw_btn_type = raw_button[0]

    pattern = re.match(r'btn(.+)(sm|cb|start)', raw_btn_type)
    if not pattern:
        return ''

    action = pattern.group(1)
    args = raw_button[1]

    if action in BUTTONS:
        text = f"\n[{name}](btn{action}:{args}*!repl!*)"
    else:
        if args:
            text = f'\n[{name}].(btn{action}:{args})'
        else:
            text = f'\n[{name}].(btn{action})'

    return text


def get_reply_msg_btns_text(message):
    text = ''
    for column in message.reply_markup.inline_keyboard:
        btn_num = 0
        for btn in column:
            btn_num += 1
            name = btn['text']

            if 'url' in btn:
                url = btn['url']
                if '?start=' in url:
                    raw_btn = url.split('?start=')[1]
                    text += parse_button(raw_btn, name)
                else:
                    text += f"\n[{btn['text']}](btnurl:{btn['url']}*!repl!*)"
            elif 'callback_data' in btn:
                text += parse_button(btn['callback_data'], name)

            if btn_num > 1:
                text = text.replace('*!repl!*', ':same')
            else:
                text = text.replace('*!repl!*', '')
    return text


async def get_msg_file(message):

    message_id = message.message_id

    tmsg = await tbot.get_messages(message.chat.id, ids=message_id)
    msg_id = tmsg.file.id

    if 'sticker' in message:
        return {'id': msg_id, 'type': 'sticker'}
    elif 'photo' in message:
        return {'id': msg_id, 'type': 'photo'}
    elif 'document' in message:
        return {'id': msg_id, 'type': 'document'}

    return None


async def get_parsed_note_list(message, split_args=1):
    note = {}
    if "reply_to_message" in message:
        # Get parsed reply msg text
        text, note['parse_mode'] = get_parsed_msg(message.reply_to_message)
        # Get parsed origin msg text
        text += ' '
        to_split = ''.join([" " + q for q in get_args(message)[:split_args]])
        if not to_split:
            to_split = ' '
        text += get_parsed_msg(message)[0].partition(message.get_command() + to_split)[2][1:]
        # Set parse_mode if origin msg override it
        if mode := get_msg_parse(message.text, default_md=False):
            note['parse_mode'] = mode

        # Get message keyboard
        if 'reply_markup' in message.reply_to_message and 'inline_keyboard' in message.reply_to_message.reply_markup:
            text += get_reply_msg_btns_text(message.reply_to_message)

        # Check on attachment
        if msg_file := await get_msg_file(message.reply_to_message):
            note['file'] = msg_file
    else:
        text, note['parse_mode'] = get_parsed_msg(message)
        to_split = ''.join([" " + q for q in get_args(message)[:split_args]])
        if not to_split:
            to_split = ' '
        text = text.partition(message.get_command() + to_split)[2]

        # Check on attachment
        if msg_file := await get_msg_file(message):
            note['file'] = msg_file

    # Preview
    if 'text' in note and '$PREVIEW' in note['text']:
        note['preview'] = True
    text = re.sub(r'%PREVIEW', '', text)

    if text.replace(' ', ''):
        note['text'] = text

    return note


async def t_unparse_note_item(message, db_item, chat_id, noformat=None, event=None):
    text = db_item['text'] if 'text' in db_item else ""

    file_id = None
    preview = None

    if 'file' in db_item:
        file_id = db_item['file']['id']

    if noformat:
        markup = None
        if 'parse_mode' not in db_item or db_item['parse_mode'] == 'none':
            text += '\n%PARSEMODE_NONE'
        elif db_item['parse_mode'] == 'html':
            text += '\n%PARSEMODE_HTML'

        if 'preview' in db_item and db_item['preview']:
            text += '\n%PREVIEW'

        db_item['parse_mode'] = None

    else:
        pm = True if message.chat.type == 'private' else False
        text, markup = button_parser(chat_id, text, pm=pm)
        if not text and not file_id:
            text = '#' + db_item['name']

        if 'parse_mode' not in db_item or db_item['parse_mode'] == 'none':
            db_item['parse_mode'] = None
        elif db_item['parse_mode'] == 'md':
            text = await vars_parser(text, message, chat_id, md=True, event=event)
        elif db_item['parse_mode'] == 'html':
            text = await vars_parser(text, message, chat_id, md=False, event=event)

        if 'preview' in db_item and db_item['preview']:
            preview = True

    return text, {
        'buttons': markup,
        'parse_mode': db_item['parse_mode'],
        'file': file_id,
        'link_preview': preview
    }


def button_parser(chat_id, texts, pm=False, aio=False, row_width=None):
    buttons = InlineKeyboardMarkup(row_width=row_width) if aio else []
    pattern = r'\[(.+?)\]\((button|btn)(.+?)(:.+?|)(:same|)\)(\n|)'
    raw_buttons = re.findall(pattern, texts)
    text = re.sub(pattern, '', texts)
    for raw_button in raw_buttons:
        name = raw_button[0]
        action = raw_button[2]
        argument = raw_button[3][1:].lower().replace('`', '') if raw_button[3] else ''

        if action in BUTTONS:
            cb = BUTTONS[action]
            string = f'{cb}_{argument}_{chat_id}' if argument else f'{cb}_{chat_id}'
            if aio:
                start_btn = InlineKeyboardButton(name, url=f'https://t.me/{BOT_USERNAME}?start=' + string)
                cb_btn = InlineKeyboardButton(name, callback_data=string)
            else:
                start_btn = Button.url(name, f'https://t.me/{BOT_USERNAME}?start=' + string)
                cb_btn = Button.inline(name, string)

            if cb.endswith('sm'):
                btn = cb_btn if pm else start_btn
            elif cb.endswith('cb'):
                btn = cb_btn
            elif cb.endswith('start'):
                btn = start_btn
            elif cb.startswith('url'):
                btn = Button.url(name, argument)
        elif action == 'url':
            if argument[0] == '/' and argument[1] == '/':
                argument = argument[2:]
            btn = InlineKeyboardButton(name, url=argument) if aio else Button.url(name, argument)
        else:
            # If btn not registred
            btn = None
            if argument:
                text += f'\n[{name}].(btn{action}:{argument})'
            else:
                text += f'\n[{name}].(btn{action})'
                continue

        if aio:
            buttons.insert(btn) if raw_button[4] else buttons.add(btn)
        else:
            if len(buttons) < 1 and raw_button[4]:
                buttons.add(btn) if aio else buttons.append([btn])
            else:
                buttons[-1].append(btn) if raw_button[4] else buttons.append([btn])

    if not aio and len(buttons) == 0:
        buttons = None

    if not text or text == ' ':  # TODO: Sometimes we can return text == ' '
        text = None

    return text, buttons


async def vars_parser(text, message, chat_id, md=False, event=None):
    if not event:
        event = message

    if not text:
        return text

    first_name = html.escape(event.from_user.first_name)
    last_name = html.escape(event.from_user.last_name or "")
    user_id = event.from_user.id
    mention = await get_user_link(user_id, md=md)
    username = '@' + (event.from_user.username or mention)

    chat_id = message.chat.id
    chat_name = html.escape(message.chat.title or 'Local')
    chat_nick = message.chat.username or chat_name
    text = text.replace('{first}', first_name) \
               .replace('{last}', last_name) \
               .replace('{fullname}', first_name + " " + last_name) \
               .replace('{id}', str(user_id).replace('{userid}', str(user_id))) \
               .replace('{mention}', mention) \
               .replace('{username}', username) \
               .replace('{chatid}', str(chat_id)) \
               .replace('{chatname}', str(chat_name)) \
               .replace('{chatnick}', str(chat_nick))
    return text
