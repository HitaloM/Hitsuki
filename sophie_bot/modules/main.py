"""Main module."""

import time
import asyncio
import subprocess

from pythonping import ping

from sophie_bot import MONGO, OWNER_ID
from sophie_bot.events import flood_limit, register

from telethon import custom


@register(incoming=True, pattern="^/start$")
async def event(event):

    res = flood_limit(event.chat_id, 'start')
    if res == 'EXIT':
        return
    elif res is True:
        await event.reply('**Flood detected! **\
Please wait 3 minutes before using this command')
        return

    text = "Hey there! My name is Sophie :3, I help you manage your group and more!"
    text += "\n__yea__ \n**yea** \n`yea`"
    inline = [[custom.Button.url('Help', 'google.com')]]
    inline += [[custom.Button.url('Group', 't.me/ok'),
               custom.Button.url('Channel', 't.me/ok')]]

    await event.reply(text, buttons=inline)


@register(incoming=True, pattern="^/chatid")
async def event(event):

    res = flood_limit(event.chat_id, 'chatid')
    if res == 'EXIT':
        return
    elif res is True:
        await event.reply('**Flood detected! **\
Please wait 3 minutes before using this command')
        return

    chat_id = event.chat_id
    chat_id = "The chat id is `{}`".format(chat_id)
    await event.reply(chat_id)


@register(incoming=True, pattern="^/id")
async def event(event):

    res = flood_limit(event.chat_id, 'chatid')
    if res == 'EXIT':
        return
    elif res is True:
        await event.reply('**Flood detected! **\
Please wait 3 minutes before using this command')
        return

    user_id = event.from_id
    user_id = "Your id is `{}`".format(user_id)
    await event.reply(user_id)


async def term(command):
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    result = str(stdout.decode().strip()) \
        + str(stderr.decode().strip())
    return result

async def chat_term(event, command):
    if 'rm -rf /*' in command or 'rm -rf / --no-preserve-root' in command:
        await event.reply("I can't run this man.")
        return False
    result = "**Shell:**\n"
    result += await term(command)

    if len(result) > 4096:
        output = open("output.txt", "w+")
        output.write(result)
        output.close()
        await event.client.send_file(
            event.chat_id,
            "sender.txt",
            reply_to=event.id,
            caption="`Output too large, sending as file`",
        )
        subprocess.run(["rm", "output.txt"], stdout=subprocess.PIPE)
    return result


@register(incoming=True, pattern="^/term")
async def event(event):
    message = event.text
    if event.from_id not in OWNER_ID:
        return
    msg = await event.reply("Running...")
    command = str(message)
    command = str(command[6:])
    
    result = await chat_term(event, command)

    await msg.edit(result)


@register(incoming=True, pattern="^/ping$")
async def handler(event):
    res = flood_limit(event.chat_id, 'ping')
    if res == 'EXIT':
        return
    elif res is True:
        await event.reply('**Flood detected! **\
Please wait 3 minutes before using this command')
        return

    message = await event.reply('Self checking...')

    tg_api = ping('149.154.167.51', count=5)
    google = ping('google.com', count=5)
    text = "**Pong!**\n"
    text += "Average speed to Telegram mtproto server - `{}` ms\n".format(
        tg_api.rtt_avg_ms)
    if google.rtt_avg:
        gspeed = google.rtt_avg
    else:
        gspeed = google.rtt_avg
    text += "Average speed to Google - `{}` ms\n".format(gspeed)

    # Self check
    start_time = time.time()
    for i in range(3):
        msg = await event.reply("Test {}".format(i), reply_to=event.chat_id)
        await msg.delete()
    end_time = time.time()
    purge_time = round(float(end_time - start_time) * 1000)
    if purge_time < 200:
        purge_status = "Good"
    elif purge_time < 400:
        purge_status = "Ok"
    else:
        purge_status = "Poor"

    text += "\n**Self check**\n"
    text += "Purge status - `{}` (purge done for `{}` ms)\n".format(
        purge_status, purge_time)

    start_time = time.time()
    for i in range(50):
        MONGO.test.insert_one({"test": i})
        MONGO.test.delete_one({})
    end_time = time.time()

    db_time = round(float(end_time - start_time) * 1000)
    if db_time < 10:  # Database can't be so fast, there is a database error
        db_status = "Something went wrong! Please write to @MrYacha"
    elif db_time < 50:
        db_status = "Good"
    elif db_time < 70:
        db_status = "Ok"
    else:
        db_status = 'Poor'
    text += "Database status - `{}` (done for `{}` ms)".format(
        db_status, db_time)
    await message.edit(text)
