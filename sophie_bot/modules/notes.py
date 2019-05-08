"""Notes module."""

import re
from time import gmtime, strftime

from bson.objectid import ObjectId

from sophie_bot import mongodb, bot
from sophie_bot.events import flood_limit, register
from sophie_bot.modules.users import is_user_admin, user_link
from sophie_bot.modules.language import get_string
from sophie_bot.modules.connections import get_conn_chat

from telethon import custom, errors, events, utils
from telethon.tl.custom import Button


@register(incoming=True, pattern="^[/!]save")
async def event(event):
    status, chat_id, chat_title = await get_conn_chat(event.from_id, event.chat_id, admin=True)
    if status is False:
        await event.reply(chat_id)
        return
    # send_id = event.chat_id

    note_name = event.message.text.split(" ", 2)[1]
    file_id = None
    if len(event.message.text.split(" ")) > 2:
        prim_text = event.message.text.split(" ", 1)[1].split(" ", 1)[1]
    else:
        prim_text = ""
    if event.message.reply_to_msg_id:
        msg = await event.get_reply_message()
        note_text = msg.message
        if prim_text:
            note_text += prim_text
        if hasattr(msg.media, 'photo'):
            file_id = utils.pack_bot_file_id(msg.media)
        if hasattr(msg.media, 'document'):
            file_id = utils.pack_bot_file_id(msg.media)
    else:
        note_text = prim_text

    status = get_string("notes", "saved", chat_id)
    old = mongodb.notes.find_one({'chat_id': chat_id, "name": note_name})
    if old:
        status = get_string("notes", "updated", chat_id)
        mongodb.notes.delete_one({'_id': old['_id']})

    date = strftime("%Y-%m-%d %H:%M:%S", gmtime())

    mongodb.notes.insert_one(
        {'chat_id': chat_id,
         'name': note_name,
         'text': note_text,
         'date': date,
         'creator': event.from_id,
         'file_id': file_id})

    new = mongodb.notes.find_one({'chat_id': chat_id, "name": note_name})['_id']
    text = get_string("notes", "note_saved_or_updated", chat_id).format(
        note_name, status, chat_title)
    text += get_string(
        "notes", "you_can_get_note", chat_id)\
        .format(name=note_name)

    if status == 'saved':
        buttons = [
            [Button.inline(get_string("notes", "del_note", chat_id), 'delnote_{}'.format(new))]
        ]
    else:
        buttons = None

    await event.reply(text, buttons=buttons)


@register(incoming=True, pattern="^[/!]clear")
async def event(event):
    chat_id = event.chat_id

    K = await is_user_admin(chat_id, event.from_id)
    if K is False:
        await event.reply(get_string(
            "notes", "dont_have_rights_to_save", chat_id))
        return

    note_name = event.message.text.split(" ", 2)[1]
    note = mongodb.notes.find_one({'chat_id': chat_id, "name": note_name})
    if note:
        mongodb.notes.delete_one({'_id': note['_id']})
        text = get_string("notes", "note_removed", chat_id).format(note_name)
    else:
        text = get_string("notes", "cant_find_note", chat_id)
    await event.reply(text)


@register(incoming=True, pattern="^[/!]noteinfo")
async def event(event):
    chat_id = event.chat_id

    K = await is_user_admin(chat_id, event.from_id)
    if K is False:
        await event.reply(get_string(
            "notes", "dont_have_rights", chat_id))
        return

    note_name = event.message.text.split(" ", 2)[1]
    note = mongodb.notes.find_one({'chat_id': chat_id, "name": note_name})
    if not note:
        text = get_string("notes", "cant_find_note", chat_id)
    else:
        text = get_string("notes", "note_info_title", chat_id)
        text += get_string("notes", "note_info_note", chat_id).format(note_name)
        text += get_string("notes", "note_info_updated", chat_id).format(
            note_name).format(note['date'])

        creator = mongodb.user_list.find_one({'user_id': note['creator']})
        if creator:
            text += get_string("notes", "note_info_by", chat_id).format(
                creator['first_name'], creator['user_id'])
        else:
            text += get_string("notes", "note_info_crt_not_cached", chat_id)

    await event.reply(text)


@register(incoming=True, pattern="^[/!]notes")
async def event(event):
    status, chat_id, chat_title = await get_conn_chat(event.from_id, event.chat_id, admin=True)
    if status is False:
        await event.reply(chat_id)
        return

    res = flood_limit(chat_id, 'notes')
    if res == 'EXIT':
        return
    elif res is True:
        await event.reply('**Flood detected! **\
Please wait 3 minutes before using this command')
        return

    notes = mongodb.notes.find({'chat_id': chat_id})
    text = get_string("notes", "notelist_header", chat_id).format(chat_title)
    if notes.count() == 0:
        text = get_string("notes", "notelist_no_notes", chat_id)
    else:
        for note in notes:
            text += "- `{}`\n".format(note['name'])
    await event.reply(text)


async def send_note(chat_id, group_id, msg_id, note_name, show_none=False, noformat=False):
    file_id = None
    note = mongodb.notes.find_one({'chat_id': int(group_id), 'name': note_name})
    if not note and show_none is True:
        await bot.send_message(chat_id, get_string(
            "notes", "note_not_found", chat_id), reply_to=msg_id)
        return
    elif not note:
        return None

    if note['file_id']:
        file_id = note['file_id']

    if not file_id:
        file_id = None

    if noformat is True:
        format = 'html'
        string = "<b>Note {}</b>\n\n".format(note_name)
        string += note['text']
        buttons = ""
    else:
        format = 'md'
        text = "**Note {}**\n\n".format(note_name)
        text += note['text']
        string, buttons = button_parser(group_id, text)

    if not buttons:
        buttons = None

    await bot.send_message(
        chat_id,
        string,
        buttons=buttons,
        parse_mode=format,
        reply_to=msg_id,
        file=file_id
    )


@bot.on(events.CallbackQuery(data=re.compile(b'delnote_')))
async def event(event):
    user_id = event.query.user_id
    K = await is_user_admin(event.chat_id, user_id)
    if K is False:
        await event.answer(get_string("notes", "dont_have_rights_to_save", event.chat_id))
        return
    note_id = re.search(r'delnote_(.*)', str(event.data)).group(1)[:-1]
    note = mongodb.notes.find_one({'_id': ObjectId(note_id)})
    if note:
        mongodb.notes.delete_one({'_id': note['_id']})

    link = user_link(user_id)
    await event.edit(get_string("notes", "note_deleted_by", event.chat_id).format(
        note['name'], link), link_preview=False)


@register(incoming=True, pattern="^[/!]get (.?)")
async def event(event):
    raw_text = event.message.raw_text.split()
    note_name = raw_text[1]
    print(len(raw_text))
    if len(raw_text) >= 3 and raw_text[2].lower() == "noformat":
        noformat = True
    else:
        noformat = False
    if len(note_name) > 1:
        await send_note(
            event.chat_id, event.chat_id, event.message.id, note_name,
            show_none=True, noformat=noformat)


@register(incoming=True, pattern="^#")
async def event(event):
    status, chat_id, chat_title = await get_conn_chat(event.from_id, event.chat_id)
    real_chat_id = event.chat_id
    if status is False:
        await event.reply(chat_id)
        return
    note_name = event.message.raw_text[1:]
    if len(note_name) > 1:
        await send_note(
            real_chat_id, chat_id, event.message.id, note_name)


def button_parser(chat_id, texts):
    buttons = []
    raw_buttons = re.findall(r'\[(.+?)\]\(button(.+?):(.+?)(:same|)\)', texts)
    text = re.sub(r'\[(.+?)\]\(button(.+?):(.+?)(:same|)\)', '', texts)
    for raw_button in raw_buttons:
        s = len(buttons)
        if raw_button[1] == 'url':
            t = [custom.Button.url(raw_button[0], raw_button[2])]
        elif raw_button[1] == 'note':
            t = [Button.inline(raw_button[0], 'get_note_{}_{}'.format(
                chat_id, raw_button[2]))]
        elif raw_button[1] == 'alert':
            t = [Button.inline(raw_button[0], 'get_alert_{}_{}'.format(
                chat_id, raw_button[2]))]
        elif raw_button[1] == 'deletemsg':
            t = [Button.inline(raw_button[0], 'get_delete_msg_{}_{}'.format(
                chat_id, raw_button[2]))]

        print(s)

        if raw_button[3]:
            new = buttons[-1] + t
            buttons = buttons[:-1]
            buttons.append(new)
        else:
            buttons.append(t)

    return text, buttons


@bot.on(events.CallbackQuery(data=re.compile(b'get_note_')))
async def event(event):
    data = str(event.data)
    event_data = re.search(r'get_note_(.*)_(.*)', data)
    notename = event_data.group(2)[:-1]
    group_id = event_data.group(1)
    user_id = event.original_update.user_id
    try:
        await send_note(user_id, group_id, None, notename)
        await event.answer("I pm'ed note to you!")
    except errors.rpcerrorlist.UserIsBlockedError or errors.rpcerrorlist.PeerIdInvalidError:
        await event.answer(
            get_string("notes", "user_blocked", event.chat_id), alert=True)


@bot.on(events.CallbackQuery(data=re.compile(b'get_alert_')))
async def event(event):
    data = str(event.data)
    event_data = re.search(r'get_alert_(.*)_(.*)', data)
    notename = event_data.group(2)[:-1]
    group_id = event_data.group(1)
    note = mongodb.notes.find_one({'chat_id': int(group_id), 'name': notename})
    if not note:
        await event.answer(get_string("notes", "cant_find_note", event.chat_id), alert=True)
        return
    text = note['text']
    if len(text) >= 200:
        await event.answer(
            get_string("notes", "note_so_big", event.chat_id), alert=True)
        return

    await event.answer(text, alert=True)


@bot.on(events.CallbackQuery(data=re.compile(b'get_delete_msg_')))
async def event(event):
    data = str(event.data)
    event_data = re.search(r'get_delete_msg_(.*)_(.*)', data)
    if 'admin' in event_data.group(2):
        user_id = event.query.user_id
        K = await is_user_admin(event.chat_id, user_id)
        if K is False:
            await event.answer(get_string("notes", "only_admins_can_rmw", event.chat_id), alert=True)
            return
    elif 'user' in event_data.group(2):
        pass
    else:
        await event.answer(
            get_string("notes", "delmsg_no_arg", event.chat_id), alert=True)
        return

    await event.delete()
