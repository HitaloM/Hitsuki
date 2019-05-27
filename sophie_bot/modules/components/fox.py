import re

import requests

from bs4 import BeautifulSoup

from telethon import custom

from sophie_bot import decorator, logger
from sophie_bot.modules.helper_func.flood import flood_limit_dec

beta_url = 'https://files.orangefox.website/OrangeFox Beta/'
stable_url = 'https://files.orangefox.website/OrangeFox-Stable/'
ext = 'zip'
fox_groups = [483808054, -1001287179850, -1001280218923, -1001155400138]
fox_beta_groups = [483808054, -1001280218923]

global DEVICES_STABLE
global DEVICES_BETA

DEVICES_STABLE = {}
DEVICES_BETA = {}


def update_devices():
    global DEVICES_STABLE
    global DEVICES_BETA

    response_stable = requests.get(stable_url, params={})
    if not response_stable.ok:
        logger.error(response_stable.raise_for_status())
        return
    response_beta = requests.get(beta_url, params={})
    if not response_beta.ok:
        logger.error(response_beta.raise_for_status())
        return

    soup_stable = BeautifulSoup(response_stable.text, 'html.parser')
    soup_beta = BeautifulSoup(response_beta.text, 'html.parser')

    stable_devices_list = re.findall(
        r'<a href="/OrangeFox-Stable/(.+?)/">.+?</a>', str(soup_stable))
    beta_devices_list = re.findall(r'<a href="/OrangeFox%20Beta/(.+?)/">.+?</a>', str(soup_beta))

    for device in stable_devices_list:

        link = stable_url + device

        raw = requests.get(link, params={})
        if not raw.ok:
            logger.error(raw)
            continue
        text = BeautifulSoup(raw.text, 'html.parser')
        builds = re.search(r"OrangeFox-(\w*)-(\w*)-(\w*)-(\w*)\.zip", str(text))
        if not builds:
            builds = re.search(r"OrangeFox-(\w*)-(\w*)-(\w*)\.zip", str(text))
            if not builds:
                builds = re.search(r">OrangeFox-(.*)\.zip", str(text))
        
        if builds[0] == ">":
            builds = builds[1:]

        link = stable_url + device + '/device_info.txt'
        raw = requests.get(link, params={})
        if not raw.ok:
            logger.error(raw)
            continue
        text = BeautifulSoup(raw.text, 'html.parser')
        codename = re.search(r"Codename: (.*)", str(text)).group(1)
        fullname = re.search(r"Device name: (.*)", str(text)).group(1)
        maintainer = re.search(r"Maintainer: (.*)", str(text)).group(1)

        DEVICES_STABLE[device] = {
            "codename": codename,
            "fullname": fullname,
            "maintainer": maintainer,
            "ver": builds.group()
        }

    for device in beta_devices_list:
        link = beta_url + device

        raw = requests.get(link, params={})
        if not raw.ok:
            logger.error(raw)
            continue
        text = BeautifulSoup(raw.text, 'html.parser')
        builds = re.search(r"OrangeFox-(\w*)-(\w*)-(\w*)-(\w*)\.zip", str(text))
        if not builds:
            builds = re.search(r"OrangeFox-(\w*)-(\w*)-(\w*)\.zip", str(text))
        link = beta_url + device + '/device_info.txt'
        raw = requests.get(link, params={})
        if not raw.ok:
            logger.error(raw)
            continue
        text = BeautifulSoup(raw.text, 'html.parser')
        codename = re.search(r"Codename: (.*)", str(text)).group(1)
        fullname = re.search(r"Device name: (.*)", str(text)).group(1)
        maintainer = re.search(r"Maintainer: (.*)", str(text)).group(1)

        DEVICES_BETA[device] = {
            "codename": codename,
            "fullname": fullname,
            "maintainer": maintainer,
            "ver": builds.group()
        }


# Main
logger.info("Update info about OrangeFox builds..")
update_devices()
logger.info("Done!")
print(DEVICES_STABLE)
print(DEVICES_BETA)


@decorator.command("listbeta")
@flood_limit_dec("listbeta")
async def listbeta(event):
    if event.chat_id not in fox_groups:
        return
    text = "**Supported beta devices:**\n"
    for device in DEVICES_BETA:
        text += "* {} (`{}`)\n".format(
            DEVICES_BETA[device]['fullname'], DEVICES_BETA[device]["codename"])
    text += "\nTo get device write `/codename`"
    await event.reply(text)


@decorator.command("list")
@flood_limit_dec("list")
async def list_stable(event):
    if event.chat_id not in fox_groups:
        return
    text = "**Supported devices:**\n"
    for device in DEVICES_STABLE:
        text += "* {} (`{}`)\n".format(
            DEVICES_STABLE[device]['fullname'], DEVICES_STABLE[device]["codename"])
    text += "\nTo get device write `/codename`"
    await event.reply(text)


@decorator.StrictCommand("^[/#](.*)")
async def check(event):
    if event.chat_id not in fox_groups:
        return
    device_arg = event.pattern_match.group(1).lower()
    if device_arg not in DEVICES_STABLE:
        return

    device = DEVICES_STABLE[device_arg]
    beta_device = DEVICES_BETA[device_arg]
    text = "**" + device['fullname'] + "** (`{}`)".format(device['codename'])
    text += "\nMaintainer: " + beta_device['maintainer']
    if event.chat_id in fox_beta_groups and device_arg in DEVICES_BETA:
        build = beta_device['ver']
        text += "\nLast beta: `" + build + "`"
        link_beta = "https://files.orangefox.website/OrangeFox%20Beta/" + device_arg
        buttons = [[custom.Button.url("Download beta", link_beta + "/" + build),
                    custom.Button.url("All builds", link_beta)]]
    else:
        build = device['ver']
        text += "\nLast build: `" + build + "`"
        link_stable = "https://files.orangefox.website/OrangeFox-Stable/" + device_arg
        buttons = [[custom.Button.url("Download last", link_stable + "/" + build)]]
        link_mirror = "https://sourceforge.net/projects/orangefox/files/"
        buttons += [[custom.Button.url("All builds", link_stable),
                    custom.Button.url("Cloud", link_mirror + device_arg)]]

    await event.reply(text, buttons=buttons)
