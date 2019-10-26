import re

from telethon import custom
from telethon.tl.custom import Button


def button_parser(chat_id, texts):
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

    return text, buttons


def get_arg(message):
    return message.get_args().split(' ')[0]


def get_args(message):
    return message.get_args().split(' ')


def need_args_dec(num=1):
    def wrapped(func):
        async def wrapped_1(event, *args, **kwargs):
            if len(event.text.split(" ")) > num:
                return await func(event, *args, **kwargs)
            else:
                await event.reply("No enoff args!")
        return wrapped_1
    return wrapped
