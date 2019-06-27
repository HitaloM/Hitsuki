from telethon import utils

RESTRICTED_SYMBOLS = ['**', '__', '`']


async def save_get_new_note(event, strings, chat_id):
    note_name = event.pattern_match.group(1)
    for sym in RESTRICTED_SYMBOLS:
        if sym in note_name:
            await event.reply(strings["notename_cant_contain"].format(sym))
            return
    if note_name[0] == "#":
        note_name = note_name[1:]
    file_id = None
    prim_text = ""
    if len(event.message.text.split(" ")) > 2:
        prim_text = event.text.partition(note_name)[2]
    if event.message.reply_to_msg_id:
        msg = await event.get_reply_message()
        if not msg:
            await event.reply(strings["bot_msg"])
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

    return note_name, file_id, note_text
