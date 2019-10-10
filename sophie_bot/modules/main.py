# Copyright © 2018, 2019 MrYacha
# This file is part of SophieBot.
#
# SophieBot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SophieBot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License

import math
import io
import subprocess
import ujson
import requests

from aiogram import types
from aiogram.utils.exceptions import PhotoDimensions

from sophie_bot import tbot, decorator
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


@decorator.register(cmds="botchanges")
@disablable_dec("botchanges")
async def botchanges(message):
    command = "git log --pretty=format:\"%an: %s\" -30"
    text = "<b>Bot changes:</b>\n"
    text += "<i>Showed last 30 commits</i>\n"
    text += await chat_term(message, command)
    await message.reply(text, parse_mode=types.ParseMode.HTML)


@decorator.register(cmds="fox")
@disablable_dec("fox")
async def random_fox(message):
    while True:
        filename = ujson.loads(requests.get('http://randomfox.ca/floof').text)['image']
        try:
            await message.reply_photo(
                types.InputFile(io.BytesIO(requests.get(filename).content)),
                caption="🦊"
            )
            return
        except PhotoDimensions:
            continue


@decorator.register(cmds="cat")
@disablable_dec("cat")
async def random_cat(message):
    while True:
        filename = ujson.loads(requests.get('http://aws.random.cat/meow').text)['file']
        try:
            await message.reply_photo(
                types.InputFile(io.BytesIO(requests.get(filename).content)),
                caption="😺"
            )
            return
        except PhotoDimensions:
            continue


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])
