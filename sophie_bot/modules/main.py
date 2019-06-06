import asyncio
import math
import subprocess

from sophie_bot import decorator, mongodb
from sophie_bot.modules.disable import disablable_dec
from sophie_bot.modules.helper_func.flood import flood_limit_dec


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


@decorator.command("botchanges")
@disablable_dec("botchanges")
@flood_limit_dec("botchanges")
async def botchanges(event):
    command = "git log --pretty=format:\"%an: %s\" -30"
    result = "**Bot changes:**\n"
    result += "__Showed last 30 commits__\n"
    result += await chat_term(event, command)
    await event.reply(result)


@decorator.command("stats")
@disablable_dec("stats")
@flood_limit_dec("stats")
async def stats(event):
    text = "**Stats**\n"
    usrs = mongodb.user_list.count()
    chats = mongodb.chat_list.count()
    text += "* `{}` total users, in `{}` chats\n".format(usrs, chats)
    text += "* `{}` total notes\n".format(mongodb.notes.count())
    text += "* `{}` total warns\n".format(mongodb.warns.count())
    text += "* `{}` total gbanned users\n".format(mongodb.blacklisted_users.count())
    text += "* `{}` chats in `{}` total feds, `{}` fbanned users\n".format(
        mongodb.fed_list.count(),
        mongodb.fed_groups.count(),
        mongodb.fbanned_users.count())
    db = mongodb.command("dbstats")
    if 'fsTotalSize' in db:
        text += '* Database size is `{}`, free `{}`'.format(
            convert_size(db['dataSize']), convert_size(db['fsTotalSize'] - db['fsUsedSize']))
    else:
        text += '* Database size is `{}`, free `512M`'.format(
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
