from telethon import utils

RESTRICTED_SYMBOLS = ['**', '__', '`']


async def save_get_new_note(message, strings, chat_id):
    args = message['text'].split(" ", 2)

    note_name = args[1]
    for sym in RESTRICTED_SYMBOLS:
        if sym in note_name:
            await message.reply(strings["notename_cant_contain"].format(sym))
            return
    if note_name[0] == "#":
        note_name = note_name[1:]
    file_id = None
    prim_text = ""
    if len(message['text'].split(" ")) > 2:
        prim_text = args[2]
    if message.reply_to_message:
        msg = message.reply_to_message
        if not msg:
            await message.reply(strings["bot_msg"])
            return
        note_text = msg.text
        if prim_text:
            note_text += prim_text
        if 'sticker' in msg:
            file_id = msg.sticker.thumb.file_id
        if 'photo' in msg:
            file_id = msg.photo.file_id
        if 'document' in msg:
            file_id = msg.document.file_id
    else:
        note_text = prim_text

    return note_name, file_id, note_text
