from datetime import datetime

from aiogram.types.inline_keyboard import InlineKeyboardMarkup, InlineKeyboardButton

from sophie_bot.decorator import register
from sophie_bot.services.mongo import db
from ..utils.get import get_similar_note
from ...utils.connections import chat_connection
from ...utils.language import get_strings_dec
from ...utils.message import get_arg, need_args_dec
from ...utils.notes import get_parsed_note_list

RESTRICTED_SYMBOLS_IN_NOTENAMES = [':', '**', '__', '`', '"', '[', ']', "'", '$', '||', '^']


@register(cmds=['save', 'setnote', 'savenote'], user_admin=True)
@need_args_dec()
@chat_connection(admin=True)
@get_strings_dec('notes')
async def save_note(message, chat, strings):
    chat_id = chat['chat_id']

    # Default settings vars
    save_aliases = False
    append_note_names = None
    note_group = None

    # Arg
    arg = get_arg(message).lower()
    if arg.startswith('+'):
        save_aliases = True
        arg = arg[1:]
    elif '+' in arg:
        arg = arg.replace((raw := arg.split('+', 1))[1], '')[:-1]
        append_note_names = raw[1].split('|')

    if '^' in arg:
        arg = arg.replace((raw := arg.split('^', 1))[1], '')[:-1]
        note_group = raw[1]

    sym = None
    if any((sym := s) in arg for s in RESTRICTED_SYMBOLS_IN_NOTENAMES):
        await message.reply(strings['notename_cant_contain'].format(symbol=sym))
        return

    note_names = arg.split('|')

    # Check for other notes have such notenames
    all_note_names = note_names
    note_names = []
    for note_name in all_note_names:
        if note_name.startswith('#'):
            note_names.append(note_name[1:])
        else:
            note_names.append(note_name)

    # Get old note
    old_note = await db.notes.find_one({'chat_id': chat_id, 'names': {'$in': note_names}})

    # Add new aliases
    if append_note_names:
        note = old_note
        if not note:
            return await message.reply(strings['no_note'])
        note['names'].extend(append_note_names)
        note['names'] = list(dict.fromkeys(note['names']))
        text = strings['note_updated']
    else:
        note = await get_parsed_note_list(message)
        note['chat_id'] = chat_id

        if old_note:
            text = strings['note_updated']
            if 'created_date' in old_note:
                note['created_date'] = old_note['created_date']
                note['created_user'] = old_note['created_user']
            note['edited_date'] = datetime.now()
            note['edited_user'] = message.from_user.id
        else:
            text = strings['note_saved']
            note['created_date'] = datetime.now()
            note['created_user'] = message.from_user.id

        if note_group:
            note['group'] = note_group
            text += strings['note_group'].format(name=f'<code>#{note_group}</code>')

        if 'text' not in note and 'file' not in note and not append_note_names:
            await message.reply(strings['blank_note'])
            return

        # Save aliases check
        note['names'] = old_note['names'] if save_aliases and old_note else note_names

    await db.notes.replace_one({'_id': old_note['_id']} if old_note else note, note, upsert=True)

    text += strings['you_can_get_note']
    text = text.format(note_name=note_names[0], chat_title=chat['chat_title'])

    # All aliases
    aliases = note_names
    if old_note:
        aliases.extend(old_note['names'])
    if append_note_names:
        aliases.extend(append_note_names)

    if len(aliases) > 1:
        text += strings['note_aliases']
        for notename in aliases:
            text += f' <code>#{notename}</code>'

    await message.reply(text)


@register(cmds=['clear', 'delnote'])
@chat_connection(admin=True)
@need_args_dec()
@get_strings_dec('notes')
async def clear_note(message, chat, strings):
    note_names = get_arg(message).lower().split('|')

    removed = ''
    not_removed = ''
    for note_name in note_names:
        if note_name[0] == '#':
            note_name = note_name[1:]

        if not (note := await db.notes.find_one({'chat_id': chat['chat_id'], 'names': {'$in': [note_name]}})):
            if len(note_names) <= 1:
                text = strings['cant_find_note'].format(chat_name=chat['chat_title'])
                if alleged_note_name := await get_similar_note(chat['chat_id'], note_name):
                    text += strings['u_mean'].format(note_name=alleged_note_name)
                await message.reply(text)
                return
            else:
                not_removed += ' #' + note_name
                continue

        await db.notes.delete_one({'_id': note['_id']})
        removed += ' #' + note_name

    if len(note_names) > 1:
        text = strings['note_removed_multiple'].format(chat_name=chat['chat_title'], removed=removed)
        if not_removed:
            text += strings['not_removed_multiple'].format(not_removed=not_removed)
        await message.reply(text)
    else:
        await message.reply(strings['note_removed'].format(note_name=note_name, chat_name=chat['chat_title']))


@register(cmds='clearall')
@chat_connection(admin=True)
@get_strings_dec('notes')
async def clear_all_notes(message, chat, strings):
    # Ensure notes count
    if not await db.notes.find_one({'chat_id': chat['chat_id']}):
        await message.reply(strings['notelist_no_notes'].format(chat_title=chat['chat_title']))
        return

    text = strings['clear_all_text'].format(chat_name=chat['chat_title'])
    buttons = InlineKeyboardMarkup()
    buttons.add(InlineKeyboardButton(strings['clearall_btn_yes'], callback_data='clean_all_notes_cb'))
    buttons.add(InlineKeyboardButton(strings['clearall_btn_no'], callback_data='cancel'))
    await message.reply(text, reply_markup=buttons)


@register(regexp='clean_all_notes_cb', f='cb', is_admin=True)
@chat_connection(admin=True)
@get_strings_dec('notes')
async def clear_all_notes_cb(event, chat, strings):
    num = (await db.notes.delete_many({'chat_id': chat['chat_id']})).deleted_count

    text = strings['clearall_done'].format(num=num, chat_name=chat['chat_title'])
    await event.message.edit_text(text)
