import math
import subprocess
import datetime

from aiogram import types

from sophie_bot import mongodb, tbot, decorator
from sophie_bot.modules.disable import disablable_dec
from sophie_bot.modules.helper_func.term import term


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
async def botchanges(message):
    command = "git log --pretty=format:\"%an: %s\" -30"
    text = "<b>Bot changes:</b>\n"
    text += "<i>Showed last 30 commits</i>\n"
    text += await chat_term(message, command)
    await message.reply(text, parse_mode=types.ParseMode.HTML)


@decorator.command("stats")
@disablable_dec("stats")
async def stats(message):
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


@decorator.t_command("owo2")
async def owo2(message):
    test = 2 / 0
    print(test)


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])
