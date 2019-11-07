import re
import html

from aiogram.types.inline_keyboard import InlineKeyboardMarkup, InlineKeyboardButton


def button_parser(chat_id, texts):
    buttons = InlineKeyboardMarkup()
    raw_buttons = re.findall(r'\[(.+?)\]\(button(.+?):(.+?)(:same|)\)', texts)
    text = re.sub(r'\[(.+?)\]\(button(.+?):(.+?)(:same|)\)', '', texts)
    for raw_button in raw_buttons:
        if raw_button[1] == 'url':
            url = raw_button[2]
            if url[0] == '/' and url[1] == '/':
                url = url[2:]
            print(raw_buttons)
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


def get_arg(message):
    return message.get_args().split(' ')[0]


def get_args(message):
    return message.get_args().split(' ')


def get_parsed_msg(message):
    if not message.text:
        return "", 'md'
    mode = get_msg_parse(message.text)
    if mode == 'html':
        # TODO: Better HTML escaping support
        # text = message.parse_entities(as_html=True)
        text = html.unescape(message.html_text)
        mode = 'html'
    elif mode == 'none':
        text = message.text
        mode = 'none'
    else:
        # text = message.parse_entities(as_html=False)
        text = message.md_text
        mode = 'md'

    text = re.sub(r'\[format:(\w+)\]', '', text)
    text = re.sub(r'$FORMAT_(\w+)', '', text)

    # WORKAROUND: Unparse buttons
    text = re.sub(r'\[(.+)\]\(\1\)', '\g<1>', text)
    text = re.sub(r'<a href=\"(.+)\">\1<\/a>', '\g<1>', text)
    text = re.sub(r'\\\[', '[', text)

    return text, mode


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


def need_args_dec(num=1):
    def wrapped(func):
        async def wrapped_1(event, *args, **kwargs):
            if len(event.text.split(" ")) > num:
                return await func(event, *args, **kwargs)
            else:
                await event.reply("No enoff args!")
        return wrapped_1
    return wrapped
