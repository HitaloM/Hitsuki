import re
from time import gmtime, strftime

from bson.objectid import ObjectId

from sophie_bot import BOT_NICK, bot, mongodb, decorator
from sophie_bot.modules.connections import get_conn_chat, connection
from sophie_bot.modules.helper_func.flood import flood_limit_dec
from sophie_bot.modules.language import get_string
from sophie_bot.modules.users import check_group_admin, user_link, is_user_admin, user_admin_dec

from telethon import custom, errors, utils
from telethon.tl.custom import Button


RESTRICTED_SYMBOLS = ['*', '_', '`']


@decorator.command("save", word_arg=True)
@user_admin_dec
@connection(admin=True)
async def save_note(event, status, chat_id, chat_title):
    note_name = event.pattern_match.group(1)
    for sym in RESTRICTED_SYMBOLS:
        if sym in note_name:
            await event.reply(get_string("notes", "notename_cant_contain", chat_id).format(sym))
            return
    if note_name[0] == "#":
        note_name = note_name[1:]
    file_id = None
    buttons = None
    prim_text = ""
    if len(event.message.text.split(" ")) > 2:
        prim_text = event.text.partition(note_name)[2]
    if event.message.reply_to_msg_id:
        msg = await event.get_reply_message()
        if not msg:
            await event.reply(get_string("notes", "bot_msg", chat_id))
            return
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
    created_date = None
    creator = None
    if old:
        if 'created' in old:
            created_date = old['created']
        if 'creator' in old:
            creator = old['creator']
        status = get_string("notes", "updated", chat_id)

    date = strftime("%Y-%m-%d %H:%M:%S", gmtime())

    if not creator:
        creator = event.from_id

    new = ({'chat_id': chat_id,
            'name': note_name,
            'text': note_text,
            'date': date,
            'created': created_date,
            'updated_by': event.from_id,
            'creator': creator,
            'file_id': file_id})

    if old:
        mongodb.notes.update_one({'_id': old['_id']}, {"$set": new}, upsert=False)
        new = None
    else:
        new = mongodb.notes.insert_one(new).inserted_id

        buttons = [
            [Button.inline(get_string("notes", "del_note", chat_id), 'delnote_{}'.format(new))]
        ]

    text = get_string("notes", "note_saved_or_updated", chat_id).format(
        note_name=note_name, status=status, chat_title=chat_title)
    text += get_string("notes", "you_can_get_note", chat_id).format(name=note_name)

    await event.reply(text, buttons=buttons)


@decorator.command("clear", arg=True)
@user_admin_dec
@connection(admin=True)
async def clear_note(event, status, chat_id, chat_title):
    note_name = event.pattern_match.group(1)
    note = mongodb.notes.delete_one({'chat_id': chat_id, "name": note_name})
    if note:
        text = get_string("notes", "note_removed", chat_id).format(
            note_name=note_name, chat_name=chat_title)
    else:
        text = get_string("notes", "cant_find_note", chat_id).format(chat_name=chat_title)
    await event.reply(text)


@decorator.command("noteinfo", arg=True)
@user_admin_dec
@connection(admin=True)
async def noteinfo(event, status, chat_id, chat_title):
    note_name = event.pattern_match.group(1)
    note = mongodb.notes.find_one({'chat_id': chat_id, "name": note_name})
    if not note:
        text = get_string("notes", "cant_find_note", chat_id)
    else:
        text = get_string("notes", "note_info_title", chat_id)
        text += get_string("notes", "note_info_note", chat_id).format(note_name=note_name)
        text += "Formatting: {note_format}\n".format(note_format=note['format'])
        text += get_string("notes", "note_info_created", chat_id).format(
            data=note['created'], user=await user_link(note['creator']))
        text += get_string("notes", "note_info_updated", chat_id).format(
            data=note['date'], user=await user_link(note['updated_by']))

    await event.reply(text)


@decorator.command("notes")
@flood_limit_dec("notes")
@connection()
async def list_notes(event, status, chat_id, chat_title):
    notes = mongodb.notes.find({'chat_id': chat_id})
    text = get_string("notes", "notelist_header", event.chat_id).format(chat_name=chat_title)
    if notes.count() == 0:
        text = get_string("notes", "notelist_no_notes", event.chat_id)
    else:
        for note in notes:
            text += "- `{}`\n".format(note['name'])
    await event.reply(text)


async def send_note(chat_id, group_id, msg_id, note_name,
                    show_none=False, noformat=False, preview=False):
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
        format = None
        string = note['text']
        buttons = ""
    else:
        string, buttons = button_parser(group_id, note['text'])
        h = re.search(r"(\[format:(markdown|md|html|none)\])", string)
        if h:
            string = string.replace(h.group(1), "")
            format_raw = h.group(2).lower()
            if format_raw == 'markdown' or format_raw == 'md':
                format = 'md'
            elif format_raw == 'html':
                format = 'html'
            elif format_raw == 'none':
                format = None
        else:
            format = 'md'

        r = re.search(r"(\[preview:(yes|no)\])", string)
        if r:
            string = string.replace(r.group(1), "")
            preview_raw = r.group(2).lower()
            if preview_raw == "yes":
                preview = True
            elif preview_raw == "no":
                preview = False

    if len(string.rstrip()) == 0:
        if noformat is True:
            string = "Note {}\n\n".format(note_name)
        else:
            string = "**Note {}**\n\n".format(note_name)

    if not buttons:
        buttons = None

    await bot.send_message(
        chat_id,
        string,
        buttons=buttons,
        parse_mode=format,
        reply_to=msg_id,
        file=file_id,
        link_preview=preview
    )


@decorator.CallBackQuery(b'delnote_', compile=True)
@flood_limit_dec("delnote_handler")
async def del_note_callback(event):
    user_id = event.query.user_id
    if await is_user_admin(event.chat_id, user_id) is False:
        return
    note_id = re.search(r'delnote_(.*)', str(event.data)).group(1)[:-1]
    note = mongodb.notes.find_one({'_id': ObjectId(note_id)})
    if note:
        mongodb.notes.delete_one({'_id': note['_id']})

    link = await user_link(user_id)
    await event.edit(get_string("notes", "note_deleted_by", event.chat_id).format(
        note_name=note['name'], user=link), link_preview=False)


@decorator.StrictCommand("^[/!#](?:get|get@{})(?: |$)(.*)".format(BOT_NICK))
async def get_note(event):
    raw_text = event.message.raw_text.split()
    note_name = raw_text[1].lower()
    if note_name[0] == "#":
        note_name = note_name[1:]
    if len(raw_text) >= 3 and raw_text[2].lower() == "noformat":
        noformat = True
    else:
        noformat = False
    if len(note_name) > 1:
        await send_note(
            event.chat_id, event.chat_id, event.message.id, note_name,
            show_none=True, noformat=noformat)


@decorator.StrictCommand("^#(.*)")
async def check_hashtag(event):
    status, chat_id, chat_title = await get_conn_chat(event.from_id, event.chat_id)
    real_chat_id = event.chat_id
    if status is False:
        await event.reply(chat_id)
        return
    note_name = event.message.raw_text[1:].lower()
    if len(note_name) > 1:
        await send_note(
            real_chat_id, chat_id, event.message.id, note_name)


def button_parser(chat_id, texts):
    buttons = []
    raw_buttons = re.findall(r'\[(.+?)\]\(button(.+?):(.+?)(:same|)\)', texts)
    text = re.sub(r'\[(.+?)\]\(button(.+?):(.+?)(:same|)\)', '', texts)
    for raw_button in raw_buttons:
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
            new = buttons[-1] + t
            buttons = buttons[:-1]
            buttons.append(new)
        else:
            buttons.append(t)

    return text, buttons


@decorator.CallBackQuery(b'get_note_')
async def get_note_callback(event):
    data = str(event.data)
    event_data = re.search(r'get_note_(.*)_(.*)', data)
    notename = event_data.group(2)[:-1]
    group_id = event_data.group(1)
    user_id = event.original_update.user_id
    try:
        await send_note(user_id, group_id, None, notename)
        await event.answer(get_string("notes", "pmed_note", event.chat_id))
    except errors.rpcerrorlist.UserIsBlockedError or errors.rpcerrorlist.PeerIdInvalidError:
        await event.answer(
            get_string("notes", "user_blocked", event.chat_id), alert=True)


@decorator.CallBackQuery(b'get_alert_')
async def get_alert_callback(event):
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


@decorator.CallBackQuery(b'get_delete_msg_')
async def del_message_callback(event):
    data = str(event.data)
    event_data = re.search(r'get_delete_msg_(.*)_(.*)', data)
    if 'admin' in event_data.group(2):
        user_id = event.query.user_id
        if await check_group_admin(event, user_id, no_msg=True) is False:
            return
    elif 'user' in event_data.group(2):
        pass
    else:
        await event.answer(
            get_string("notes", "delmsg_no_arg", event.chat_id), alert=True)
        return

    await event.delete()
