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


def need_args_dec(num=1):
    def wrapped(func):
        async def wrapped_1(event, *args, **kwargs):
            if len(event.text.split(" ")) > num:
                return await func(event, *args, **kwargs)
            else:
                await event.reply("No enoff args!")
        return wrapped_1
    return wrapped
