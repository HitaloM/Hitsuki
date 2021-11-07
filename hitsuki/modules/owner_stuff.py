# Copyright (C) 2018 - 2020 MrYacha. All rights reserved. Source code available under the AGPL.
# Copyright (C) 2021 HitaloSama.
# Copyright (C) 2019 Aiogram.
#
# This file is part of Hitsuki (Telegram Bot)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from contextlib import suppress
import traceback
import asyncio
import signal
import shutil
import html
import sys
import os

import requests
import rapidjson

from time import gmtime, strftime
from meval import meval
from io import BytesIO

from aiogram.utils.exceptions import BadRequest, Unauthorized

from hitsuki import OWNER_ID, OPERATORS, HITSUKI_VERSION, bot, dp
from hitsuki.decorator import REGISTRED_COMMANDS, COMMANDS_ALIASES, register
from hitsuki.modules import LOADED_MODULES
from hitsuki.services.mongo import db, mongodb
from hitsuki.services.redis import redis
from hitsuki.services.telethon import tbot
from hitsuki.config import get_str_key
from hitsuki.utils.channel_logs import channel_log
from .utils.covert import convert_size
from .utils.language import get_strings_dec
from .utils.message import need_args_dec
from .utils.notes import BUTTONS, get_parsed_note_list, t_unparse_note_item, send_note
from .utils.term import chat_term, term
from .utils.user_details import get_chat_dec


@register(cmds='botchanges', is_op=True)
async def botchanges(message):
    command = "git log --pretty=format:\"%an: %s\" -30"
    text = "<b>Bot changes:</b>\n"
    text += "<i>Showed last 30 commits</i>\n"
    text += await chat_term(message, command)
    await message.reply(text, disable_web_page_preview=True)


@register(cmds='allcommands', is_op=True)
async def all_commands_list(message):
    text = "".join("* /" + cmd + "\n" for cmd in REGISTRED_COMMANDS)
    await message.reply(text)


@register(cmds='allcmdsaliases', is_op=True)
async def all_cmds_aliases_list(message):
    text = ""
    text = str(COMMANDS_ALIASES)
    await message.reply(text)


@register(cmds='loadedmodules', is_op=True)
async def all_modules_list(message):
    text = "".join("* " + module.__name__ + "\n" for module in LOADED_MODULES)
    await message.reply(text)


@register(cmds='avaiblebtns', is_op=True)
async def all_btns_list(message):
    text = "Avaible message inline btns:\n"
    for module in BUTTONS:
        text += "* " + module + "\n"
    await message.reply(text)


@register(cmds='ip', is_owner=True, only_pm=True)
async def get_bot_ip(message):
    await message.reply(requests.get("http://ipinfo.io/ip").text)


@register(cmds="term", is_owner=True)
async def cmd_term(message):
    msg = await message.reply("Running...")
    command = str(message.text.split(" ", 1)[1])
    text = "<b>Shell:</b>\n"
    text += "<code>" + html.escape(await chat_term(message, command), quote=False) + "</code>"
    with suppress(BadRequest):
        await msg.edit_text(text)


@register(cmds="leavechat", is_owner=True)
@get_chat_dec()
@need_args_dec()
async def leave_chat(message, chat):
    c = await db.chat_list.find_one({"chat_id": chat["chat_id"]})
    try:
        await bot.leave_chat(chat_id=chat["chat_id"])
    except Unauthorized:
        await message.reply("I couldn't access chat/channel! Maybe I was kicked from there!")
        return
    await message.reply("Done!")
    await channel_log(f"I left the group <b>{c['chat_title']}</b>", info_log=False)


@register(cmds="sbroadcast", is_owner=True)
@need_args_dec()
async def sbroadcast(message):
    data = await get_parsed_note_list(message, split_args=-1)
    dp.register_message_handler(check_message_for_smartbroadcast)

    await db.sbroadcast.drop({})

    chats = mongodb.chat_list.distinct('chat_id')

    data['chats_num'] = len(chats)
    data['recived_chats'] = 0
    data['chats'] = chats

    await db.sbroadcast.insert_one(data)
    await message.reply("Smart broadcast planned for <code>{}</code> chats".format(len(chats)))


@register(cmds="stopsbroadcast", is_owner=True)
async def stop_sbroadcast(message):
    dp.message_handlers.unregister(check_message_for_smartbroadcast)
    old = await db.sbroadcast.find_one({})
    await db.sbroadcast.drop({})
    await message.reply(
        "Smart broadcast stopped."
        "It was sended to <code>%d</code> chats." % old['recived_chats']
    )


@register(cmds="continuebroadcast", is_owner=True)
async def continue_sbroadcast(message):
    dp.register_message_handler(check_message_for_smartbroadcast)
    return await message.reply("Re-registered the broadcast handler.")


# Check on smart broadcast
async def check_message_for_smartbroadcast(message):
    chat_id = message.chat.id
    if not (db_item := await db.sbroadcast.find_one({'chats': {'$in': [chat_id]}})):
        return

    text, kwargs = await t_unparse_note_item(message, db_item, chat_id)
    await send_note(chat_id, text, **kwargs)

    await db.sbroadcast.update_one({'_id': db_item['_id']}, {'$pull': {'chats': chat_id}, '$inc': {'recived_chats': 1}})


@register(cmds="purgecache", is_owner=True)
async def purge_caches(message):
    redis.flushdb()
    await message.reply("Redis cache was cleaned.")


@register(cmds="stopbot", is_owner=True)
async def bot_stop(message):
    await message.reply("Goodbye...")
    os.kill(os.getpid(), signal.SIGINT)


@register(cmds="restart", is_owner=True)
async def restart_bot(message):
    m = await message.reply("Hitsuki will be restarted...")
    args = [sys.executable, "-m", "hitsuki"]
    await m.edit_text("See you later...")
    os.execl(sys.executable, *args)


@register(cmds="upgrade", is_owner=True)
async def upgrade(message):
    m = await message.reply("Upgrading sources...")
    proc = await asyncio.create_subprocess_shell("git pull --no-edit",
                                                 stdout=asyncio.subprocess.PIPE,
                                                 stderr=asyncio.subprocess.STDOUT)
    stdout = (await proc.communicate())[0]
    if proc.returncode == 0:
        if "Already up to date." in stdout.decode():
            await m.edit_text("There's nothing to upgrade.")
        else:
            await m.edit_text("Restarting...")
            args = [sys.executable, "-m", "hitsuki"]
            os.execl(sys.executable, *args)
    else:
        await m.edit_text(f"Upgrade failed (process exited with {proc.returncode}):\n{stdout.decode()}")
        proc = await asyncio.create_subprocess_shell("git merge --abort")
        await proc.communicate()


@register(cmds="backup", is_owner=True)
async def backup_now(message):
    await do_backup(message.chat.id, message.message_id)


async def do_backup(chat_id, reply=False):
    if reply:
        await bot.send_message(chat_id, "Dumping the DB, please wait...", reply_to_message_id=reply)
    date = strftime("%Y-%m-%d_%H:%M:%S", gmtime())
    file_name = f"backups/dump_{date}.7z"
    if not os.path.exists("backups/tempbackup/"):
        os.makedirs("backups/tempbackup/")
    MONGO_URI = get_str_key("MONGO_URI")
    await term(f'mongodump --uri "mongodb://{MONGO_URI}" --out=backups/tempbackup')

    # Copy config file
    shutil.copyfile('data/bot_conf.yaml', 'backups/tempbackup/bot_conf.yaml')

    if reply:
        await bot.send_message(chat_id, "Compressing and uploading to Telegram...", reply_to_message_id=reply)
    password = get_str_key("BACKUP_PASS")
    await term(f"cd backups/tempbackup/; 7z a -mx9 ../../{file_name} * -p{password} -mhe=on")
    shutil.rmtree('backups/tempbackup')

    if not os.path.exists(file_name):
        await bot.send_message(chat_id, "Error!", reply_to_message_id=reply)
        return

    text = "<b>Backup created!</b>"
    size = convert_size(os.path.getsize(file_name))
    text += f"\nBackup name: <code>{file_name}</code>"
    text += f"\nSize: <code>{size}</code>"
    await tbot.send_file(
        chat_id,
        file_name,
        reply_to=reply,
        caption=text,
        parse_mode="html"
    )
    shutil.rmtree('backups')


@register(cmds="eval", is_owner=True)
@need_args_dec()
async def on_eval_m(message):
    command = message.text.split()[0]
    eval_code = message.text[len(command) + 1 :]
    sm = await message.reply("Running...")
    try:
        stdout = await meval(eval_code, globals(), **locals())
    except BaseException:
        error = traceback.format_exc()
        await sm.edit_text(
            f"An error occurred while running the code:\n<code>{html.escape(error)}</code>"
        )
        return
    lines = str(stdout).split("\n")
    output = "".join(f"<code>{html.escape(line)}</code>\n" for line in lines)
    output_message = f"<b>Input\n&gt;</b> <code>{html.escape(eval_code)}</code>\n\n"
    if len(output) > 0:
        if len(output) > (4096 - len(output_message)):
            document = BytesIO(
                (output.replace("<code>", "").replace("</code>", "")).encode()
            )
            document.name = "output.txt"
            await tbot.send_file(message.chat.id, document, reply_to=message.message_id)
        else:
            output_message += f"<b>Output\n&gt;</b> {output}"
    await sm.edit_text(output_message)


@register(cmds="upload", is_owner=True)
async def upload_file(message):
    input_str = message.get_args()
    if not os.path.exists(input_str):
        await message.reply("File not found!")
        return
    await message.reply("Processing ...")
    caption_rts = os.path.basename(input_str)
    with open(input_str, 'rb') as f:
        await tbot.send_file(
            message.chat.id,
            f,
            caption=caption_rts,
            force_document=False,
            allow_cache=False,
            reply_to=message.message_id
        )


@register(cmds="crash", is_owner=True)
async def crash(message):
    test = 2 / 0
    print(test)


@register(cmds="event", is_op=True)
async def get_event(message):
    print(message)
    event = str(rapidjson.dumps(message, indent=2))
    await message.reply(event)


@register(cmds="stats", is_op=True)
async def stats(message):
    text = f"<b>Hitsuki {HITSUKI_VERSION} stats</b>\n"

    for module in [m for m in LOADED_MODULES if hasattr(m, '__stats__')]:
        text += await module.__stats__()

    await message.reply(text)


async def __stats__():
    text = ""
    if os.getenv('WEBHOOKS', False):
        text += f"* Webhooks mode, listen port: <code>{os.getenv('WEBHOOKS_PORT', 8080)}</code>\n"
    else:
        text += "* Long-polling mode\n"
    text += "* Database structure version <code>{}</code>\n".format(
        (await db.db_structure.find_one({}))['db_ver']
    )
    local_db = await db.command("dbstats")
    if 'fsTotalSize' in local_db:
        text += '* Database size is <code>{}</code>, free <code>{}</code>\n'.format(
            convert_size(local_db['dataSize']),
            convert_size(local_db['fsTotalSize'] - local_db['fsUsedSize'])
        )
    else:
        text += '* Database size is <code>{}</code>, free <code>{}</code>\n'.format(
            convert_size(local_db['storageSize']),
            convert_size(536870912 - local_db['storageSize'])
        )

    text += "* <code>{}</code> total keys in Redis database\n".format(
        len(redis.keys()))
    text += "* <code>{}</code> total commands registred, in <code>{}</code> modules\n".format(
        len(REGISTRED_COMMANDS), len(LOADED_MODULES))
    return text


@get_strings_dec('owner_stuff')
async def __user_info__(message, user_id, strings):
    if user_id == OWNER_ID:
        return strings["father"]
    if user_id in OPERATORS:
        return strings['sudo_crown']
