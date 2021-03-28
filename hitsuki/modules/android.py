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

import time
import rapidjson as json
from bs4 import BeautifulSoup
from hurry.filesize import size as get_size

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from hitsuki import decorator
from hitsuki.decorator import register
from .utils.android import GetDevice
from .utils.disable import disableable_dec
from .utils.message import get_arg, get_cmd
from .utils.language import get_strings_dec
from .utils.http import http

# Commands /evo and /los ported from Haruka Aya
# Commands /twrp, /samcheck and /samget ported from Samsung Geeks


@register(cmds="los")
@disableable_dec("los")
@get_strings_dec("android")
async def los(message, strings):

    try:
        device = get_arg(message)
    except IndexError:
        device = ""

    if device == "":
        text = strings["cmd_example"].format(cmd=get_cmd(message))
        await message.reply(text, disable_web_page_preview=True)
        return

    fetch = await http.get(f"https://download.lineageos.org/api/v1/{device}/nightly/*")
    if fetch.status_code == 200 and len(fetch.json()["response"]) != 0:
        usr = json.loads(fetch.content)
        response = usr["response"][0]
        filename = response["filename"]
        url = response["url"]
        buildsize_a = response["size"]
        buildsize_b = get_size(int(buildsize_a))
        version = response["version"]

        text = (strings["download"]).format(url=url, filename=filename)
        text += (strings["build_size"]).format(size=buildsize_b)
        text += (strings["version"]).format(version=version)

        btn = strings["dl_btn"]
        keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton(text=btn, url=url))
        await message.reply(text, reply_markup=keyboard, disable_web_page_preview=True)
        return

    else:
        text = strings["err_query"]
    await message.reply(text, disable_web_page_preview=True)


@decorator.register(cmds=["evo", "evox"])
@disableable_dec("evo")
@get_strings_dec("android")
async def evo(message, strings):

    try:
        device = get_arg(message)
    except IndexError:
        device = ""

    if device == "x00t":
        device = "X00T"

    if device == "x01bd":
        device = "X01BD"

    if device == "":
        text = strings["cmd_example"].format(cmd=get_cmd(message))
        await message.reply(text, disable_web_page_preview=True)
        return

    fetch = await http.get(
        f"https://raw.githubusercontent.com/Evolution-X-Devices/official_devices/master/builds/{device}.json"
    )

    if fetch.status_code in [500, 504, 505]:
        await message.reply(strings["err_github"])
        return

    if fetch.status_code == 200:
        try:
            usr = json.loads(fetch.content)
            filename = usr["filename"]
            url = usr["url"]
            version = usr["version"]
            maintainer = usr["maintainer"]
            maintainer_url = usr["telegram_username"]
            size_a = usr["size"]
            size_b = get_size(int(size_a))

            text = (strings["download"]).format(url=url, filename=filename)
            text += (strings["build_size"]).format(size=size_b)
            text += (strings["android_version"]).format(version=version)
            text += (strings["maintainer"]).format(
                name=f"<a href='{maintainer_url}'>{maintainer}</a>"
            )

            btn = strings["dl_btn"]
            keyboard = InlineKeyboardMarkup().add(
                InlineKeyboardButton(text=btn, url=url)
            )
            await message.reply(
                text, reply_markup=keyboard, disable_web_page_preview=True
            )
            return

        except ValueError:
            text = strings["err_ota"]
            await message.reply(text, disable_web_page_preview=True)
            return

    elif fetch.status_code == 404:
        text = strings["err_query"]
        await message.reply(text, disable_web_page_preview=True)
        return


@register(cmds="whatis")
@disableable_dec("whatis")
@get_strings_dec("android")
async def whatis(message, strings):
    device = get_arg(message)
    if not device:
        text = strings["cmd_example"].format(cmd=get_cmd(message))
        await message.reply(text)
        return

    data = await GetDevice(device).get()
    if data:
        name = data["name"]
        device = data["device"]
        brand = data["brand"]
        model = data["model"]
    else:
        text = strings["err_query"]
        await message.reply(text)
        return

    text = strings["whatis"].format(device=device, brand=brand, name=name)
    await message.reply(text)


@decorator.register(cmds=["models", "variants"])
@disableable_dec("models")
@get_strings_dec("android")
async def variants(message, strings):
    device = get_arg(message)
    if not device:
        text = strings["cmd_example"].format(cmd=get_cmd(message))
        await message.reply(text)
        return

    data = await GetDevice(device).get()
    if data:
        name = data["name"]
        device = data["device"]
    else:
        text = strings["err_query"]
        await message.reply(text)
        return

    data = await http.get(
        "https://raw.githubusercontent.com/androidtrackers/certified-android-devices/master/by_device.json"
    )
    db = json.loads(data.content)
    device = db[device]
    text = f"<b>{name}</b> variants:\n\n"

    for i in device:
        name = i["name"]
        model = i["model"]
        text += strings["variants"].format(model=model, name=name)

    await message.reply(text)


@register(cmds="magisk")
@disableable_dec("magisk")
@get_strings_dec("android")
async def magisk(message, strings):
    url = "https://raw.githubusercontent.com/topjohnwu/magisk_files/"
    releases = strings["magisk"]
    variant = ["master/stable", "master/beta", "canary/canary"]
    for variants in variant:
        fetch = await http.get(url + variants + ".json")

        if fetch.status_code in [500, 504, 505]:
            await message.reply(strings["err_github"])
            return

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
            releases += f'{name}: <a href="{url}{branch}/{data["magisk"]["link"]}">v{data["magisk"]["version"]}</a> (<code>{data["magisk"]["versionCode"]}</code>) | '
        else:
            releases += f'{name}: <a href="{data["magisk"]["link"]}">v{data["magisk"]["version"]}</a> (<code>{data["magisk"]["versionCode"]}</code>) | '

        if cc == 1:
            releases += (
                f'<a href="{url}{branch}/{data["uninstaller"]["link"]}">Uninstaller</a> | '
                f'<a href="{url}{branch}/{data["magisk"]["note"]}">Changelog</a>\n'
            )
        else:
            releases += (
                f'<a href="{data["uninstaller"]["link"]}">Uninstaller</a>\n'
                f'<a href="{data["magisk"]["note"]}">Changelog</a>\n'
            )

    await message.reply(releases, disable_web_page_preview=True)


@register(cmds="phh")
@disableable_dec("phh")
@get_strings_dec("android")
async def phh(message, strings):
    fetch = await http.get(
        "https://api.github.com/repos/phhusson/treble_experimentations/releases/latest"
    )

    if fetch.status_code in [500, 504, 505]:
        await message.reply(strings["err_github"])
        return

    usr = json.loads(fetch.content)
    text = strings["phh"]
    for i in range(len(usr)):
        try:
            name = usr["assets"][i]["name"]
            url = usr["assets"][i]["browser_download_url"]
            text += f"<a href='{url}'>{name}</a>\n"
        except IndexError:
            continue

    await message.reply(text)


@register(cmds="phhmagisk")
@disableable_dec("phhmagisk")
@get_strings_dec("android")
async def phh_magisk(message, strings):
    fetch = await http.get(
        "https://api.github.com/repos/expressluke/phh-magisk-builder/releases/latest"
    )

    if fetch.status_code in [500, 504, 505]:
        await message.reply(strings["err_github"])
        return

    usr = json.loads(fetch.content)
    text = strings["phhmagisk"]
    for i in range(len(usr)):
        try:
            name = usr["assets"][i]["name"]
            url = usr["assets"][i]["browser_download_url"]
            tag = usr["tag_name"]
            size_bytes = usr["assets"][i]["size"]
            size = float("{:.2f}".format((size_bytes / 1024) / 1024))
            text += f"<b>Tag:</b> <code>{tag}</code>\n"
            text += f"<b>Size</b>: <code>{size} MB</code>\n\n"
            btn = strings["dl_btn"]
            button = InlineKeyboardMarkup().add(InlineKeyboardButton(text=btn, url=url))
        except IndexError:
            continue

    await message.reply(text, reply_markup=button)
    return


@register(cmds="twrp")
@disableable_dec("twrp")
@get_strings_dec("android")
async def twrp(message, strings):
    device = get_arg(message).lower()

    if not device:
        text = strings["cmd_example"].format(cmd=get_cmd(message))
        await message.reply(text)
        return

    url = await http.get(f"https://eu.dl.twrp.me/{device}/")
    if url.status_code == 404:
        text = strings["err_twrp"].format(device=device)
        await message.reply(text)
        return

    else:
        text = strings["twrp_header"]
        text += f"  <b>Device:</b> {device}\n"
        page = BeautifulSoup(url.content, "lxml")
        date = page.find("em").text.strip()
        text += f"  <b>Updated:</b> <code>{date}</code>\n"
        trs = page.find("table").find_all("tr")
        row = 2 if trs[0].find("a").text.endswith("tar") else 1

        for i in range(row):
            download = trs[i].find("a")
            dl_link = f"https://dl.twrp.me{download['href']}"
            dl_file = download.text
            size = trs[i].find("span", {"class": "filesize"}).text
        text += f"  <b>Size:</b> <code>{size}</code>\n"
        text += f"  <b>File:</b> <code>{dl_file.lower()}</code>"
        btn = strings["dl_btn"]
        button = InlineKeyboardMarkup().add(InlineKeyboardButton(text=btn, url=dl_link))

        await message.reply(text, reply_markup=button)


@decorator.register(cmds=["samcheck", "samget"])
@disableable_dec("samcheck")
@get_strings_dec("android")
async def check(message, strings):
    try:
        msg_args = message.text.split()
        temp = msg_args[1]
        csc = msg_args[2]
    except IndexError:
        text = strings["sam_cmd_example"].format(cmd=get_cmd(message))
        await message.reply(text)
        return

    model = "sm-" + temp if not temp.upper().startswith("SM-") else temp
    fota = await http.get(
        f"http://fota-cloud-dn.ospserver.net/firmware/{csc.upper()}/{model.upper()}/version.xml"
    )
    test = await http.get(
        f"http://fota-cloud-dn.ospserver.net/firmware/{csc.upper()}/{model.upper()}/version.test.xml"
    )
    if test.status_code != 200:
        text = strings["err_sam"].format(model=temp.upper(), csc=csc.upper())
        await message.reply(text)
        return

    page1 = BeautifulSoup(fota.content, "lxml")
    page2 = BeautifulSoup(test.content, "lxml")
    os1 = page1.find("latest").get("o")
    os2 = page2.find("latest").get("o")
    if page1.find("latest").text.strip():
        pda1, csc1, phone1 = page1.find("latest").text.strip().split("/")
        text = f"<b>MODEL:</b> <code>{model.upper()}</code>\n<b>CSC:</b> <code>{csc.upper()}</code>\n\n"
        text += strings["sam_latest"]
        text += f"• PDA: <code>{pda1}</code>\n• CSC: <code>{csc1}</code>\n"
        if phone1:
            text += f"• Phone: <code>{phone1}</code>\n"
        if os1:
            text += f"• Android: <code>{os1}</code>\n"
        text += "\n"
    else:
        text = strings["err_pub_sam"].format(model=model.upper(), csc=csc.upper())
    text += strings["sam_test"]
    if len(page2.find("latest").text.strip().split("/")) == 3:
        pda2, csc2, phone2 = page2.find("latest").text.strip().split("/")
        text += f"• PDA: <code>{pda2}</code>\n• CSC: <code>{csc2}</code>\n"
        if phone2:
            text += f"• Phone: <code>{phone2}</code>\n"
        if os2:
            text += f"• Android: <code>{os2}</code>\n"
    else:
        md5 = page2.find("latest").text.strip()
        text += f"• Hash: <code>{md5}</code>\n• Android: <code>{os2}</code>\n"

    if get_cmd(message) == "samcheck":
        await message.reply(text)

    elif get_cmd(message) == "samget":
        text += strings["sam_down_from"]
        buttons = InlineKeyboardMarkup()
        buttons.insert(
            InlineKeyboardButton(
                "SamMobile",
                url="https://www.sammobile.com/samsung/firmware/{}/{}/".format(
                    model.upper(), csc.upper()
                ),
            )
        )
        buttons.insert(
            InlineKeyboardButton(
                "SamFw",
                url="https://samfw.com/firmware/{}/{}/".format(
                    model.upper(), csc.upper()
                ),
            )
        )
        buttons.insert(
            InlineKeyboardButton(
                "SamFrew",
                url="https://samfrew.com/model/{}/region/{}/".format(
                    model.upper(), csc.upper()
                ),
            )
        )

        await message.reply(text, reply_markup=buttons)


@decorator.register(cmds=["ofox", "of"])
@disableable_dec("ofox")
@get_strings_dec("android")
async def orangefox(message, strings):
    API_HOST = "https://api.orangefox.download/v3/"
    try:
        args = message.text.split()
        codename = args[1].lower()
    except BaseException:
        codename = ""
    try:
        build_type = args[2].lower()
    except BaseException:
        build_type = ""

    if build_type == "":
        build_type = "stable"

    if codename == "devices" or codename == "":
        text = (
            f"<b>OrangeFox Recovery <i>{build_type}</i> is currently avaible for:</b>"
        )
        data = await http.get(
            API_HOST + f"devices/?release_type={build_type}&sort=device_name_asc"
        )
        devices = json.loads(data.text)
        try:
            for device in devices["data"]:
                text += (
                    f"\n - {device['full_name']} (<code>{device['codename']}</code>)"
                )
        except BaseException:
            await message.reply(
                f"'<b>{build_type}</b>' is not a type of build available, the types are just '<b>beta</b>' or '<b>stable</b>'."
            )
            return

        if build_type == "stable":
            text += (
                "\n\n"
                + f"To get the latest Stable release use <code>/ofox (codename)</code>, for example: <code>/ofox raphael</code>"
            )
        elif build_type == "beta":
            text += (
                "\n\n"
                + f"To get the latest Beta release use <code>/ofox (codename) beta</code>, for example: <code>/ofox raphael beta</code>"
            )
        await message.reply(text)
        return

    data = await http.get(API_HOST + f"devices/get?codename={codename}")
    device = json.loads(data.text)
    if data.status_code == 404:
        await message.reply("Device is not found!")
        return

    data = await http.get(
        API_HOST
        + f"releases/?codename={codename}&type={build_type}&sort=date_desc&limit=1"
    )
    if data.status_code == 404:
        btn = "Device's page"
        url = f"https://orangefox.download/device/{device['codename']}"
        button = InlineKeyboardMarkup().add(InlineKeyboardButton(text=btn, url=url))
        await message.reply(
            f"⚠️ There is no '<b>{build_type}</b>' releases for <b>{device['full_name']}</b>.",
            reply_markup=button,
            disable_web_page_preview=True,
        )
        return

    find_id = json.loads(data.text)
    for build in find_id["data"]:
        file_id = build["_id"]

    data = await http.get(API_HOST + f"releases/get?_id={file_id}")
    release = json.loads(data.text)
    if data.status_code == 404:
        await message.reply("Release is not found!")
        return

    text = f"<u><b>OrangeFox Recovery <i>{build_type}</i> release</b></u>\n"
    text += ("  <b>Device:</b> {fullname} (<code>{codename}</code>)\n").format(
        fullname=device["full_name"], codename=device["codename"]
    )
    text += ("  <b>Version:</b> {}\n").format(release["version"])
    text += ("  <b>Release date:</b> {}\n").format(
        time.strftime("%d/%m/%Y", time.localtime(release["date"]))
    )

    text += ("  <b>Maintainer:</b> {name}\n").format(name=device["maintainer"]["name"])
    changelog = release["changelog"]
    try:
        text += "  <u><b>Changelog:</b></u>\n"
        for entry_num in range(len(changelog)):
            if entry_num == 10:
                break
            text += f"    - {changelog[entry_num]}\n"
    except BaseException:
        pass

    btn = strings["dl_btn"]
    url = release["mirrors"]["DL"]
    button = InlineKeyboardMarkup().add(InlineKeyboardButton(text=btn, url=url))
    await message.reply(text, reply_markup=button, disable_web_page_preview=True)
    return


__mod_name__ = "Android"

__help__ = """
Module specially made for Android users.

<b>GSI</b>
- /phh: Get the latest PHH AOSP GSIs.
- /phhmagisk: Get the latest PHH Magisk.

<b>Device firmware:</b>
- /samcheck (model) (csc): Samsung only - shows the latest firmware info for the given device, taken from samsung servers.
- /samget (model) (csc): Similar to the <code>/samcheck</code> command but having download buttons.

<b>Misc</b>
- /magisk: Get latest Magisk releases.
- /twrp (codename): Gets latest TWRP for the android device using the codename.
- /ofox (codename): Gets latest OFRP for the android device using the codename.
- /ofox devices: Sends the list of devices with stable releases supported by OFRP.
- /models (codename): Search for Android device models using codename.
- /whatis (codename): Find out which smartphone is using the codename.
"""
