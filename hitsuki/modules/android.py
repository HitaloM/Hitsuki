# This file is part of Hitsuki (Telegram Bot)

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

import rapidjson as json
from requests import get

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import Message

from hitsuki import bot
from hitsuki.decorator import register
from .utils.disable import disableable_dec
from .utils.message import need_args_dec, get_args_str


@register(cmds='magisk')
@disableable_dec('magisk')
async def magisk(message):
    url = 'https://raw.githubusercontent.com/topjohnwu/magisk_files/'
    releases = '<b>Latest Magisk Releases:</b>\n'
    variant = ['master/stable', 'master/beta', 'canary/canary']
    for variants in variant:
        fetch = get(url + variants + '.json')
        data = json.loads(fetch.content)
        if variants == "master/stable":
            name = "<b>Stable</b>"
            cc = 0
            branch = "master"
        elif variants == "master/beta":
            name = "<b>Beta</b>"
            cc = 0
            branch = "master"
        elif variants == "canary/canary":
            name = "<b>Canary</b>"
            cc = 1
            branch = "canary"

        if variants == "canary/canary":
            releases += f'{name}: <a href="{url}{branch}/{data["magisk"]["link"]}">ZIP v{data["magisk"]["version"]}</a> | ' \
                        f'<a href="{url}{branch}/{data["app"]["link"]}">APK v{data["app"]["version"]}</a> | '
        else:
            releases += f'{name}: <a href="{url}{branch}/{data["magisk"]["link"]}">ZIP v{data["magisk"]["version"]}</a> | ' \
                        f'<a href="{data["app"]["link"]}">APK v{data["app"]["version"]}</a> | '

        if cc == 1:
            releases += f'<a href="{url}{branch}/{data["uninstaller"]["link"]}">Uninstaller</a> | ' \
                        f'<a href="{url}{branch}/notes.md">Changelog</a>\n'
        else:
            releases += f'<a href="{data["uninstaller"]["link"]}">Uninstaller</a>\n'

    await message.reply(releases, disable_web_page_preview=True)
