"""Main module."""

import time
import asyncio

from sophie_bot import MONGO, OWNER_ID
from sophie_bot.events import flood_limit, register
from sophie_bot.modules.users import user_link

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


@register(incoming=True, pattern="^/id ?(.*)")
async def event(event):

    res = flood_limit(event.chat_id, 'id')
    if res == 'EXIT':
        return
    elif res is True:
        await event.reply('**Flood detected! **\
Please wait 3 minutes before using this command')
        return

    text = "**ID's:**\n"
    text += "Your id - `{}`\n".format(event.from_id)
    text += "Chat id - `{}`\n".format(event.chat_id)
    text += "Your message id - `{}`\n".format(event.message.id)

    #TODO: Normal args...
    if event.message.text == '/id':
        await event.reply(text)
        return

    elif event.message.reply_to_msg_id:
        msg = await event.get_reply_message()
        text += "\n**Replied message:**\n"
        user = MONGO.user_list.find_one({'user_id': msg.from_id})
        userl = await user_link(msg.from_id)
        text += "{}'s user id - `{}`\n".format(userl, msg.from_id)
        text += "{}'s message id - `{}`".format(userl, msg.id)

    else:
        user, lol = await get_user_and_text(event)
        lol = lol # No prevent pylint warn ;-;
        user_link = "[{}](https://t.me/{})'s".format(user['first_name'], user['user_id'])
        text += "{} user id - `{}`\n".format(user_link, user['user_id'])
    
    await event.reply(text)
    

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
    result = await term(command)

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


@register(incoming=True, pattern="^/botchanges")
async def event(event):
    res = flood_limit(event.chat_id, 'botchanges')
    if res == 'EXIT':
        return
    elif res is True:
        await event.reply('**Flood detected! **\
Please wait 3 minutes before using this command')
        return
    command = "git log --pretty=format:\"%an: %s\" "
    result = await chat_term(event, command)
    await event.reply(result)