# Copyright (C) 2019 The Raphielscape Company LLC.
# Copyright (C) 2018-2019 MrYacha
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

from aiogram.types.input_file import InputFile

from sophie_bot import bot
from sophie_bot.decorator import register
from .utils.disable import disablable_dec
from .utils.language import get_strings_dec


@register(cmds='getsticker')
@disablable_dec('getsticker')
@get_strings_dec('stickers')
async def get_sticker(message, strings):
    if 'reply_to_message' not in message or 'sticker' not in message.reply_to_message:
        await message.reply(strings['rpl_to_sticker'])
        return

    sticker = message.reply_to_message.sticker
    file_id = sticker.file_id
    text = strings['ur_sticker'].format(emoji=sticker.emoji, id=file_id)

    sticker_file = await bot.download_file_by_id(file_id, io.BytesIO())

    await message.reply_document(
        InputFile(sticker_file, filename=f'{sticker.set_name}_{sticker.file_id[:5]}.png'),
        text
    )
