
# Copyright © 2019 MrYacha
# Copyright © 2019 baalajimaestro (Telegram-UserBot)
# Copyright © 2019 raphielscape (Telegram-UserBot)
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

import asyncio

from sys import executable
from os import remove

from telethon.sync import events, TelegramClient

from sophie_bot import NAME, API_ID, API_HASH

ubot = TelegramClient(NAME + '_userbot', API_ID, API_HASH)
ubot.start()


@ubot.on(events.NewMessage(pattern=r'^\.\.alive', outgoing=True))
async def ubot_alive(event):
    await event.reply('Sophie micro_userbot is alive!')


@ubot.on(events.NewMessage(pattern=r"^\.\.exec(?: |$)([\s\S]*)", outgoing=True))
async def run(event):
    """ For .exec command, which executes the dynamically created program """
    code = event.pattern_match.group(1)

    if not code:
        await event.edit("``` At least a variable is required to \
execute. Use .help exec for an example.```")
        return

    if code in ("userbot.session", "config.env"):
        await event.edit("`That's a dangerous operation! Not Permitted!`")
        return

    if len(code.splitlines()) <= 5:
        codepre = code
    else:
        clines = code.splitlines()
        codepre = clines[0] + "\n" + clines[1] + "\n" + clines[2] + \
            "\n" + clines[3] + "..."

    command = "".join(f"\n {l}" for l in code.split("\n.strip()"))
    process = await asyncio.create_subprocess_exec(
        executable,
        '-c',
        command.strip(),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()
    result = str(stdout.decode().strip()) \
        + str(stderr.decode().strip())

    if result:
        if len(result) > 4096:
            file = open("output.txt", "w+")
            file.write(result)
            file.close()
            await event.client.send_file(
                event.chat_id,
                "output.txt",
                reply_to=event.id,
                caption="`Output too large, sending as file`",
            )
            remove("output.txt")
            return
        await event.edit("**Sophie micro_userbot query: **\n`"
                         f"{codepre}"
                         "`\n**Result: **\n`"
                         f"{result}"
                         "`")
    else:
        await event.edit("**Sophie micro_userbot query: **\n`"
                         f"{codepre}"
                         "`\n**Result: **\n`No Result Returned/False`")