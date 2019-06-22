import asyncio
import os

from sophie_bot import OWNER_ID, tbot, decorator, mongodb, redis, logger, dp
from sophie_bot.modules.users import user_owner_dec
from sophie_bot.modules.main import chat_term
from sophie_bot.modules.notes import button_parser

from aiogram import types


@dp.message_handler(commands=['term'])
@user_owner_dec
async def term(message: types.Message):
    msg = await message.reply("Running...")
    command = str(message['text'].split(" ", 1)[1])
    result = "<b>Shell:</b>\n"
    result += await chat_term(message, command)
    await msg.edit_text(result, parse_mode=types.ParseMode.HTML)


@decorator.command("broadcast", arg=True, from_users=OWNER_ID)
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
            await tbot.send_message(chat['chat_id'], text, buttons=buttons)
            num_succ = num_succ + 1
        except Exception as err:
            num_fail = num_fail + 1
            await msg.edit("Error:\n`{}`.\nBroadcasting will continues.".format(err))
            await asyncio.sleep(2)
            await msg.edit("Broadcasting to {} chats...".format(chats.count()))
    await msg.edit(
        "**Broadcast completed!** Message sended to `{}` chats successfully, \
`{}` didn't received message.".format(num_succ, num_fail))


@decorator.command("sbroadcast", arg=True, from_users=OWNER_ID)
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


@decorator.command("stopsbroadcast", from_users=OWNER_ID)
async def stop_sbroadcast(event):
    old = mongodb.sbroadcast_settings.find_one({})
    mongodb.sbroadcast_list.drop()
    mongodb.sbroadcast_settings.drop()
    await event.reply("Smart broadcast stopped."
                      "It was sended to `{}` chats.".format(
                          old['recived_chats']))


# Check on smart broadcast
@decorator.insurgent()
async def check_message_for_smartbroadcast(event):
    chat_id = event.chat_id
    match = mongodb.sbroadcast_list.find_one({'chat_id': chat_id})
    if match:
        try:
            raw_text = mongodb.sbroadcast_settings.find_one({})['text']
            text, buttons = button_parser(event.chat_id, raw_text)
            if len(buttons) == 0:
                buttons = None
            await tbot.send_message(chat_id, text, buttons=buttons)
        except Exception as err:
            logger.error(err)
        mongodb.sbroadcast_list.delete_one({'chat_id': chat_id})
        old = mongodb.sbroadcast_settings.find_one({})
        num = old['recived_chats'] + 1
        mongodb.sbroadcast_settings.update(
            {'_id': old['_id']}, {
                'text': old['text'],
                'all_chats': old['all_chats'],
                'recived_chats': num
            }, upsert=False)


@decorator.command("backup", from_users=OWNER_ID)
async def backup(event):
    msg = await event.reply("Running...")
    date = await chat_term(event, "date \"+%Y-%m-%d.%H:%M:%S\"")
    await chat_term(event, "mongodbdump --gzip --archive > Backups/dump_{}.gz".format(date))
    await msg.edit("**Done!**\nBackup under `Backups/dump_{}.gz`".format(date))


@decorator.command("purgecaches?(s)", from_users=OWNER_ID)
async def purge_caches(event):
    redis.flushdb()
    await event.reply("redis cache was cleaned.")


@decorator.command("botstop", from_users=OWNER_ID)
async def bot_stop(event):
    await event.reply("Goodbye...")
    exit(1)


@decorator.command("upload", arg=True, from_users=OWNER_ID)
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
