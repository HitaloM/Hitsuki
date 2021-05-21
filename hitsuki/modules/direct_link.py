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

import re

from bs4 import BeautifulSoup

from hitsuki.decorator import register

from .utils.disable import disableable_dec
from .utils.http import http
from .utils.language import get_strings_dec
from .utils.message import get_arg, get_cmd


@register(cmds="direct")
@disableable_dec("direct")
@get_strings_dec("direct_links")
async def direct_link_generator(message, strings):
    text = get_arg(message)

    if not text:
        await message.reply(strings["cmd_example"].format(cmd=get_cmd(message)))
        return

    links = re.findall(r"\bhttps?://.*\.\S+", text)

    reply = []
    if not links:
        await message.reply(strings["no_link"])
        return

    for link in links:
        if "sourceforge.net" in link:
            reply.append(await sourceforge(link, strings))
        else:
            reply.append(
                re.findall(r"\bhttps?://(.*?[^/]+)", link)[0] + " is not supported"
            )

    await message.reply("\n".join(reply))


async def sourceforge(url: str, strings) -> str:
    try:
        link = re.findall(r"\bhttps?://.*sourceforge\.net\S+", url)[0]
    except IndexError:
        reply = strings["no_sf_link"]
        return reply

    file_path = re.findall(r"/files(.*)/download", link)
    if not file_path:
        file_path = re.findall(r"/files(.*)", link)
    try:
        file_path = file_path[0]
    except IndexError:
        reply = strings["sf_link_error"]
        return reply
    reply = f"Mirrors for <code>{file_path.split('/')[-1]}</code>\n"
    project = re.findall(r"projects?/(.*?)/files", link)[0]
    mirrors = (
        f"https://sourceforge.net/settings/mirror_choices?"
        f"projectname={project}&filename={file_path}"
    )
    response = await http.get(mirrors)
    page = BeautifulSoup(response.content, "lxml")
    info = page.find("ul", {"id": "mirrorList"}).findAll("li")

    for mirror in info[1:]:
        name = re.findall(r"\((.*)\)", mirror.text.strip())[0]
        dl_url = (
            f'https://{mirror["id"]}.dl.sourceforge.net/project/{project}/{file_path}'
        )
        reply += f'<a href="{dl_url}">{name}</a> '
    return reply
