import asyncio
import os

from sophie_bot import bot, mongodb, redis, Decorator
from sophie_bot.modules.main import chat_term
from sophie_bot.modules.notes import button_parser
from sophie_bot.modules.helper_func.user_status import is_user_owner


@Decorator.command("term", arg=True)
@is_user_owner
async def term(event):
    msg = await event.reply("Running...")
    command = str(event.message.text.split(" ", 1)[1])
    result = "**Shell:**\n"
    result += await chat_term(event, command)
    await msg.edit(result)


@Decorator.command("broadcast", arg=True)
@is_user_owner
async def broadcast(event):
    chats = mongodb.chat_list.find({})
    raw_text = event.message.text.split(" ", 1)[1]
    text, buttons = button_parser(event.chat_id, raw_text)
    if len(buttons) == 0:
        buttons = None
    msg = await event.reply("Broadcasting to {} chats...".format(chats.count()))
    num_succ = 0
    num_fail = 0
    for chat in chats:
        try:
            await bot.send_message(chat['chat_id'], text, buttons=buttons)
            num_succ = num_succ + 1
        except Exception as err:
            num_fail = num_fail + 1
            await msg.edit("Error:\n`{}`.\nBroadcasting will continues.".format(err))
            await asyncio.sleep(2)
            await msg.edit("Broadcasting to {} chats...".format(chats.count()))
    await msg.edit(
        "**Broadcast completed!** Message sended to `{}` chats successfully, \
`{}` didn't received message.".format(num_succ, num_fail))


@Decorator.command("sbroadcast", arg=True)
@is_user_owner
async def sbroadcast(event):
    text = event.message.text.split(" ", 1)[1]
    # Add chats to sbroadcast list
    chats = mongodb.chat_list.find({})
    mongodb.sbroadcast_list.drop()
    mongodb.sbroadcast_settings.drop()
    for chat in chats:
        mongodb.sbroadcast_list.insert_one({'chat_id': chat['chat_id']})
    mongodb.sbroadcast_settings.insert_one({
        'text': text,
        'all_chats': chats.count(),
        'recived_chats': 0
    })
    await event.reply(
        "Smart broadcast planned for `{}` chats".format(chats.count()))

# Check on smart broadcast
@Decorator.insurgent()
async def check_message_for_smartbroadcast(event):
    chat_id = event.chat_id
    match = mongodb.sbroadcast_list.find_one({'chat_id': chat_id})
    if match:
        try:
            raw_text = mongodb.sbroadcast_settings.find_one({})['text']
            text, buttons = button_parser(event.chat_id, raw_text)
            if len(buttons) == 0:
                buttons = None
            await bot.send_message(chat_id, text, buttons=buttons)
        except Exception as err:
            print(err)
        mongodb.sbroadcast_list.delete_one({'chat_id': chat_id})
        old = mongodb.sbroadcast_settings.find_one({})
        num = old['recived_chats'] + 1
        mongodb.sbroadcast_settings.update(
            {'_id': old['_id']}, {
                'text': old['text'],
                'all_chats': old['all_chats'],
                'recived_chats': num
            }, upsert=False)


@Decorator.command("backup", arg=True)
@is_user_owner
async def backup(event):
    msg = await event.reply("Running...")
    date = await chat_term(event, "date \"+%Y-%m-%d.%H:%M:%S\"")
    await chat_term(event, "mongodbdump --gzip --archive > Backups/dump_{}.gz".format(date))
    await msg.edit("**Done!**\nBackup under `Backups/dump_{}.gz`".format(date))


@Decorator.command("purgecaches?(s)", arg=True)
@is_user_owner
async def purge_caches(event):
    redis.flushdb()
    await event.reply("redis cache was cleaned.")


@Decorator.command("botstop", arg=True)
@is_user_owner
async def bot_stop(event):
    await event.reply("Goodbye...")
    exit(1)


@Decorator.command("upload", arg=True)
@is_user_owner
async def upload_file(event):
    input_str = event.pattern_match.group(1)
    if os.path.exists(input_str):
        await event.reply("Processing ...")
        if os.path.exists(input_str):
            caption_rts = os.path.basename(input_str)
            myfile = open(input_str, 'rb')
            await event.client.send_file(
                event.chat_id,
                myfile,
                caption=caption_rts,
                force_document=False,
                allow_cache=False,
                reply_to=event.message.id
            )
