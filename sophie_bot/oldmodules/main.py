# Copyright (C) 2019 The Raphielscape Company LLC.
# Copyright (C) 2018 - 2019 MrYacha
#
# This file is part of SophieBot.
#
# SophieBot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.

import io
import math
import subprocess

import requests
import ujson
from aiogram import types
from aiogram.utils.exceptions import PhotoDimensions
from sophie_bot.modules.disable import disablable_dec
from sophie_bot.modules.helper_func.term import term

from sophie_bot import tbot, decorator


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
