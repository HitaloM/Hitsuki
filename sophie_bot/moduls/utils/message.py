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

import re
import html
import sys

from .tmarkdown_converter import tbold, titalic, tpre, tcode, tlink

from aiogram.types.inline_keyboard import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types.message_entity import MessageEntityType
from aiogram.types import fields
from aiogram.utils import markdown


def button_parser(chat_id, texts):
    buttons = InlineKeyboardMarkup()
    raw_buttons = re.findall(r'\[(.+?)\]\(button(.+?):(.+?)(:same|)\)', texts)
    text = re.sub(r'\[(.+?)\]\(button(.+?):(.+?)(:same|)\)', '', texts)
    for raw_button in raw_buttons:
        if raw_button[1] == 'url':
            url = raw_button[2]
            if url[0] == '/' and url[1] == '/':
                url = url[2:]
            t = InlineKeyboardButton(raw_button[0], url=url)
        elif raw_button[1] == 'note':
            t = InlineKeyboardButton(raw_button[0], callback_data='get_note_{}_{}'.format(chat_id, raw_button[2]))
        elif raw_button[1] == 'alert':
            t = InlineKeyboardButton(raw_button[0], callback_data='get_alert_{}_{}'.format(chat_id, raw_button[2]))
        elif raw_button[1] == 'deletemsg':
            t = InlineKeyboardButton(raw_button[0], callback_data='get_delete_msg_{}_{}'.format(chat_id, raw_button[2]))

        if raw_button[3]:
            buttons.insert(t)
        else:
            buttons.add(t)

    return text, buttons


def tbutton_parser(chat_id, texts):
    buttons = []
    raw_buttons = re.findall(r'\[(.+?)\]\(button(.+?):(.+?)(:same|)\)', texts)
    text = re.sub(r'\[(.+?)\]\(button(.+?):(.+?)(:same|)\)', '', texts)
    for raw_button in raw_buttons:
        if raw_button[1] == 'url':
            url = raw_button[2]
            if url[0] == '/' and url[0] == '/':
                url = url[2:]
            t = [custom.Button.url(raw_button[0], url)]
        elif raw_button[1] == 'note':
            t = [Button.inline(raw_button[0], 'get_note_{}_{}'.format(
                chat_id, raw_button[2]))]
        elif raw_button[1] == 'alert':
            t = [Button.inline(raw_button[0], 'get_alert_{}_{}'.format(
                chat_id, raw_button[2]))]
        elif raw_button[1] == 'deletemsg':
            t = [Button.inline(raw_button[0], 'get_delete_msg_{}_{}'.format(
                chat_id, raw_button[2]))]

        if raw_button[3]:
            new = buttons[-1] + t
            buttons = buttons[:-1]
            buttons.append(new)
        else:
            buttons.append(t)

    if len(buttons) == 0:
        buttons = None

    return text, buttons


def get_arg(message):
    return message.get_args().split(' ')[0]


def get_args(message):
    return message.get_args().split(' ')


def tparse_ent(ent, text, as_html=True):
    if not text:
        return text

    type = ent.type
    offset = ent.offset
    length = ent.length

    if sys.maxunicode == 0xffff:
        return text[offset:offset + length]

    if not isinstance(text, bytes):
        entity_text = text.encode('utf-16-le')
    else:
        entity_text = text

    entity_text = entity_text[offset * 2:(offset + length) * 2].decode('utf-16-le')

    if type == 'bold':
        method = markdown.hbold if as_html else tbold
        return method(entity_text)
    if type == 'italic':
        method = markdown.hitalic if as_html else titalic
        return method(entity_text)
    if type == 'pre':
        method = markdown.hpre if as_html else tpre
        return method(entity_text)
    if type == 'code':
        method = markdown.hcode if as_html else tcode
        return method(entity_text)
    if type == 'url':
        method = markdown.hlink if as_html else tlink
        return method(entity_text, entity_text)
    if type == 'text_link':
        method = markdown.hlink if as_html else tlink
        return method(entity_text, ent.url)
    if type == 'text_mention' and ent.user:
        return ent.user.get_mention(entity_text, as_html=as_html)

    return entity_text


def get_parsed_msg(message):
    if not message.text:
        return None, 'md'

    text = message.text or message.caption

    mode = get_msg_parse(text)
    if mode == 'html':
        as_html = True
    else:
        as_html = False

    quote_fn = markdown.quote_html if as_html else markdown.escape_md
    entities = message.entities or message.caption_entities

    if not entities:
        return quote_fn(text), mode

    if not sys.maxunicode == 0xffff:
        text = text.encode('utf-16-le')

    result = ''
    offset = 0

    for entity in sorted(entities, key=lambda item: item.offset):
        entity_text = tparse_ent(entity, text, as_html=as_html)

        if sys.maxunicode == 0xffff:
            part = text[offset:entity.offset]
            result += quote_fn(part) + entity_text
        else:
            part = text[offset * 2:entity.offset * 2].decode('utf-16-le')
            result += quote_fn(part) + entity_text

        offset = entity.offset + entity.length

    if sys.maxunicode == 0xffff:
        part = text[offset:]
        result += quote_fn(part)
    else:
        part = text[offset * 2:]
        result += quote_fn(part.decode('utf-16-le'))

    result = re.sub(r'\[format:(\w+)\]', '', result)
    result = re.sub(r'$FORMAT_(\w+)', '', result)

    return result, mode


def get_msg_parse(text, default_md=True):
    if '[format:html]' in text or '$FORMAT_HTML' in text:
        return 'html'
    elif '[format:none]' in text or '$FORMAT_NONE' in text:
        return 'none'
    elif '[format:md]' in text or '$FORMAT_MD' in text:
        return 'md'
    else:
        if not default_md:
            return None
        return 'md'


def get_reply_msg_btns_text(message):
    text = ''
    for column in message.reply_markup.inline_keyboard:
        btn_num = 0
        for btn in column:
            btn_num += 1
            if btn_num > 1:
                text += "\n[{}](buttonurl:{}:same)".format(
                    btn['text'], btn['url']
                )
            else:
                text += "\n[{}](buttonurl:{})".format(
                    btn['text'], btn['url']
                )
    return text


def get_msg_file(message):
    if 'sticker' in message:
        return {'id': message.sticker.file_id, 'type': 'sticker'}
    elif 'photo' in message:
        return {'id': message.photo[1].file_id, 'type': 'photo'}
    elif 'document' in message:
        return {'id': message.document.file_id, 'type': 'document'}

    return None


def get_parsed_note_list(message):
    note = {}
    if "reply_to_message" in message:
        # Get parsed reply msg text
        text, note['parse_mode'] = get_parsed_msg(message.reply_to_message)
        # Get parsed origin msg text
        text += ' '
        text += get_parsed_msg(message)[0].partition(
            message.get_command() + ' ' + get_arg(message)
        )[2][1:]
        # Set parse_mode if origin msg override it
        if mode := get_msg_parse(message.text, default_md=False):
            note['parse_mode'] = mode

        # Get message keyboard
        if 'reply_markup' in message.reply_to_message and 'inline_keyboard' in message.reply_to_message.reply_markup:
            text += get_reply_msg_btns_text(message.reply_to_message)

        # Check on attachment
        if msg_file := get_msg_file(message.reply_to_message):
            note['file'] = msg_file
    else:
        text, note['parse_mode'] = get_parsed_msg(message)
        text = text.partition(message.get_command() + ' ' + get_arg(message))[2]

        # Check on attachment
        if msg_file := get_msg_file(message):
            note['file'] = msg_file

    if text.replace(' ', ''):
        note['text'] = text

    return note


def need_args_dec(num=1):
    def wrapped(func):
        async def wrapped_1(event, *args, **kwargs):
            if len(event.text.split(" ")) > num:
                return await func(event, *args, **kwargs)
            else:
                await event.reply("No enoff args!")
        return wrapped_1
    return wrapped
