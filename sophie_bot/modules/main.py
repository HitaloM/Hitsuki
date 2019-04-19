"""Main module."""

import time
import asyncio
import subprocess

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
        msg = await event.reply("Running...")
        await asyncio.sleep(2)
        await msg.edit("Blyat can't do it becuase u dumb.")
        return
    msg = await event.reply("Running...")
    command = str(message)
    command = str(command[6:])
    
    result = await chat_term(event, command)

    await msg.edit(result)
