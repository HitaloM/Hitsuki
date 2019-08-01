import asyncio
import math
import subprocess
import sys
import io
import traceback
import ujson
import datetime

from time import gmtime, strftime, time

from sophie_bot import mongodb, tbot, decorator, dp, logger
from sophie_bot.modules.disable import disablable_dec

from aiogram import types


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


async def chat_term(message, command):
    result = await term(command)
    if len(result) > 4096:
        output = open("output.txt", "w+")
        output.write(result)
        output.close()
        await tbot.send_file(
            message.chat.id,
            "output.txt",
            reply_to=message['message_id'],
            caption="`Output too large, sending as file`",
        )
        subprocess.run(["rm", "output.txt"], stdout=subprocess.PIPE)
    return result


@decorator.command("botchanges")
@disablable_dec("botchanges")
async def botchanges(message, **kwargs):
    command = "git log --pretty=format:\"%an: %s\" -30"
    text = "<b>Bot changes:</b>\n"
    text += "<i>Showed last 30 commits</i>\n"
    text += await chat_term(message, command)
    await message.reply(text, parse_mode=types.ParseMode.HTML)


@decorator.command("stats")
@disablable_dec("stats")
async def stats(message, **kwargs):
    text = "*Stats*\n"
    usrs = mongodb.user_list.count()
    chats = mongodb.chat_list.count()
    text += "\* `{}` total users, in `{}` chats\n".format(usrs, chats)

    users_added = mongodb.user_list.find({
        'first_detected_date': {'$gte': datetime.datetime.now() - datetime.timedelta(days=2)}
    }).count()

    chats_added = mongodb.chat_list.find({
        'first_detected_date': {'$gte': datetime.datetime.now() - datetime.timedelta(days=2)}
    }).count()

    text += "\* `{}` new users and `{}` new chats in the last 48 hours\n".format(
        users_added, chats_added
    )
    text += "\* `{}` total notes\n".format(mongodb.notes.count())
    text += "\* `{}` total warns\n".format(mongodb.warns.count())
    text += "\* `{}` total gbanned users\n".format(mongodb.blacklisted_users.count())
    text += "\* `{}` chats in `{}` total feds, `{}` fbanned users\n".format(
        mongodb.fed_groups.count(),
        mongodb.fed_list.count(),
        mongodb.fbanned_users.count())
    text += "\* `{}` total crash happened in this week\n".format(
        mongodb.errors.find({
            'date': {'$gte': datetime.datetime.now() - datetime.timedelta(days=7)}
        }).count())
    db = mongodb.command("dbstats")
    if 'fsTotalSize' in db:
        text += '\* Database size is `{}`, free `{}`'.format(
            convert_size(db['dataSize']), convert_size(db['fsTotalSize'] - db['fsUsedSize']))
    else:
        text += '\* Database size is `{}`, free `{}`'.format(
            convert_size(db['storageSize']), convert_size(536870912 - db['storageSize']))
    await message.reply(text, parse_mode=types.ParseMode.MARKDOWN)


@dp.errors_handler()
async def all_errors_handler(message, dp):
    date = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    logger.error("Error: " + date)

    new = {
        'error': str(sys.exc_info()[1]),
        'date': datetime.datetime.now()
    }
    mongodb.errors.insert_one(new)

    msg = message.message

    text = "<b>Sorry, I got a error!</b>\n"
    link = "<a href=\"https://t.me/YanaBotGroup\">Sophie support chat</a>"
    text += f"If you wanna you can report it - just forward this file to {link}.\n"
    text += "I won't log anything except the fact of error and date\n"

    ftext = "Sophie error log file."
    ftext += "\n______________________\n"
    ftext += "\nNotice:\nThis file uploaded ONLY here, we logged only fact of error and date, "
    ftext += "we respect your privacy, you may not report this error if you've "
    ftext += "any confidential data here, noone will see your data\n\n"
    ftext += "\nDate: " + date
    ftext += "\nGroup ID: " + str(msg.chat.id)
    ftext += "\nSender ID: " + str(msg.from_user.id)
    ftext += "\n\nRaw update text:\n"
    ftext += str(message)
    ftext += "\n\nFormatted update text:\n"
    ftext += str(ujson.dumps(msg, indent=2))
    ftext += "\n\nTraceback info:\n"
    ftext += str(traceback.format_exc())
    ftext += "\n\nError text:\n"
    ftext += str(sys.exc_info()[1])

    command = "git log --pretty=format:\"%an: %s\" -5"
    ftext += "\n\n\nLast 5 commits:\n"
    ftext += await term(command)

    await msg.answer_document(
        types.InputFile(io.StringIO(ftext), filename="error.txt"),
        text,
        reply=msg.message_id
    )

    return


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])
