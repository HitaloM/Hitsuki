import asyncio
import math
import subprocess

from sophie_bot import mongodb, bot
from sophie_bot.events import flood_limit, register


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
        await event.reply("I can't run this, man.")
        return False
    result = await term(command)

    if len(result) > 4096:
        output = open("output.txt", "w+")
        output.write(result)
        output.close()
        await event.client.send_file(
            event.chat_id,
            "output.txt",
            reply_to=event.id,
            caption="`Output too large, sending as file`",
        )
        subprocess.run(["rm", "output.txt"], stdout=subprocess.PIPE)
    return result


@register(incoming=True, pattern="^[/!]botchanges")
async def botchanges(event):
    res = flood_limit(event.chat_id, 'botchanges')
    if res == 'EXIT':
        return
    elif res is True:
        await event.reply('**Flood detected! **\
Please wait 3 minutes before using this command')
        return
    command = "git log --pretty=format:\"%an: %s\" -30"
    result = "**Bot changes:**\n"
    result += "__Showed last 30 commits__\n"
    result += await chat_term(event, command)
    await event.reply(result)


@register(incoming=True, pattern="^[/!]stats")
async def stats(event):
    res = flood_limit(event.chat_id, 'stats')
    if res == 'EXIT':
        return
    elif res is True:
        await event.reply('**Flood detected! **\
Please wait 3 minutes before using this command')
        return

    text = "**Stats**\n"
    usrs = mongodb.user_list.count()
    chats = mongodb.chat_list.count()
    text += "{} total users, in {} chats\n".format(usrs, chats)
    db = mongodb.command("dbstats")
    if hasattr(db, 'fsTotalSize'):
        text += 'Database size is {}, free {}'.format(
            convert_size(db['dataSize']), convert_size(db['fsTotalSize'] - db['fsUsedSize']))
    else:
        text += 'Database size is {}, free 512M'.format(
            convert_size(db['storageSize']))
    await event.reply(text)



def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])
