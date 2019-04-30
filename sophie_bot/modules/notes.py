"""Notes module."""

import re
from time import gmtime, strftime

from bson.objectid import ObjectId

from sophie_bot import MONGO, bot
from sophie_bot.events import flood_limit, register
from sophie_bot.modules.users import is_user_admin
from sophie_bot.modules.language import get_string

from telethon import custom, errors, events, utils
from telethon.tl.custom import Button


@register(incoming=True, pattern="^/save")
async def event(event):
    chat_id = event.chat_id
    K = await is_user_admin(chat_id, event.from_id)
    if K is False:
        await event.reply(get_string("notes", "no_right_save_note", chat_id))
        return

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
    old = MONGO.notes.find_one({'chat_id': chat_id, "name": note_name})
    if old:
        status = get_string("notes", "updated", chat_id)
        MONGO.notes.delete_one({'_id': old['_id']})

    date = strftime("%Y-%m-%d %H:%M:%S", gmtime())

    MONGO.notes.insert_one(
        {'chat_id': chat_id,
         'name': note_name,
         'text': note_text,
         'date': date,
         'creator': event.from_id,
         'file_id': file_id})

    new = MONGO.notes.find_one({'chat_id': chat_id, "name": note_name})['_id']
    text = get_string("notes", "note_saved_or_updated", chat_id).format(note_name, status)
    text += get_string(
        "notes", "you_can_get_note", chat_id)\
        .format(name=note_name)

    if status == 'saved':
        buttons = [
            [Button.inline('Delete note', 'delnote_{}'.format(new))]]
    else:
        buttons = None

    await event.reply(text, buttons=buttons)


@register(incoming=True, pattern="^/clear")
async def event(event):
    chat_id = event.chat_id

    K = await is_user_admin(chat_id, event.from_id)
    if K is False:
        await event.reply(get_string(
            "notes", "dont_have_rights_to_save", chat_id))
        return

    note_name = event.message.text.split(" ", 2)[1]
    note = MONGO.notes.find_one({'chat_id': chat_id, "name": note_name})
    if note:
        MONGO.notes.delete_one({'_id': note['_id']})
        text = "Note {} removed!".format(note_name)
    else:
        text = "I can't find this note!"
    await event.reply(text)


@register(incoming=True, pattern="^/noteinfo")
async def event(event):
    chat_id = event.chat_id

    K = await is_user_admin(chat_id, event.from_id)
    if K is False:
        await event.reply(get_string(
            "notes", "dont_have_rights", chat_id))
        return

    note_name = event.message.text.split(" ", 2)[1]
    note = MONGO.notes.find_one({'chat_id': chat_id, "name": note_name})
    if not note:
        text = "I can't find this note!"
    else:
        text = "**Note info**\n"
        text += "Note: `{}`\n".format(note_name)
        text += "Last updated in: `{}`\n".format(note['date'])

        creator = MONGO.user_list.find_one({'user_id': note['creator']})
        if creator:
            text += "Created by: {} (`{}`)\n".format(
                creator['first_name'], creator['user_id'])
        else:
            text += "Creator not cached, I can't find him.\n"

    await event.reply(text)


@register(incoming=True, pattern="^/notes")
async def event(event):

    res = flood_limit(event.chat_id, 'notes')
    if res == 'EXIT':
        return
    elif res is True:
        await event.reply('**Flood detected! **\
Please wait 3 minutes before using this command')
        return

    notes = MONGO.notes.find({'chat_id': event.chat_id})
    text = get_string("notes", "notelist_header", event.chat_id)
    if notes.count() == 0:
        text = get_string("notes", "notelist_no_notes", event.chat_id)
    else:
        for note in notes:
            text += "- `{}`\n".format(note['name'])
    await event.reply(text)


async def send_note(chat_id, group_id, msg_id, note_name, show_none=False, noformat=False):
    file_id = None
    note = MONGO.notes.find_one({'chat_id': int(group_id), 'name': note_name})
    if not note and show_none is True:
        await bot.send_message(chat_id, "Note not found!", reply_to=msg_id)
        return
    elif not note:
        return None

    if note['file_id']:
        file_id = note['file_id']

    if not file_id:
        file_id = None

    if noformat is True:
        format = 'html'
        text = "<b>Note {}</b>\n\n".format(note_name)
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
        await event.answer("You don't have rights to save notes here!")
        return
    note_id = re.search(r'delnote_(.*)', str(event.data)).group(1)[:-1]
    note = MONGO.notes.find_one({'_id': ObjectId(note_id)})
    if note:
        MONGO.notes.delete_one({'_id': note['_id']})

    user = await bot.get_entity(user_id)
    link = "[{}](tg://user?id={})".format(user.first_name, user_id)
    await event.edit("Note {} deleted by {}.".format(
        note['name'], link), link_preview=False)


@register(incoming=True, pattern="^/get (.?)")
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
    note_name = event.message.raw_text[1:]
    if len(note_name) > 1:
        await send_note(
            event.chat_id, event.chat_id, event.message.id, note_name)


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

        if raw_button[3]:
            buttons.insert(s - 1, buttons[s - 1] + t)
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
            "Write /start in my pm and click on button again!", alert=True)


@bot.on(events.CallbackQuery(data=re.compile(b'get_alert_')))
async def event(event):
    data = str(event.data)
    event_data = re.search(r'get_alert_(.*)_(.*)', data)
    notename = event_data.group(2)[:-1]
    group_id = event_data.group(1)
    note = MONGO.notes.find_one({'chat_id': int(group_id), 'name': notename})
    if not note:
        await event.answer("I can't find this note!", alert=True)
        return
    text = note['text']
    if len(text) >= 200:
        await event.answer(
            "This note bigger than Telegram limit of 200 symbols!", alert=True)
        return

    await event.answer(text, alert=True)


@bot.on(events.CallbackQuery(data=re.compile(b'get_delete_msg_')))
async def event(event):
    await event.delete()
