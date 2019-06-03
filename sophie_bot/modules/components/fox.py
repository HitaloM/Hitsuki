from ftplib import FTP

from telethon import custom

from sophie_bot import OWNER_ID, CONFIG, decorator, logger
from sophie_bot.modules.users import user_link
from sophie_bot.modules.helper_func.flood import flood_limit_dec

ftp_url = "ftp.orangefox.website"
fox_groups = [483808054, -1001287179850, -1001280218923, -1001155400138, -1001362128194]
fox_beta_groups = [483808054, -1001280218923, -1001362128194]

global DEVICES_STABLE
global DEVICES_BETA

DEVICES_STABLE = {}
DEVICES_BETA = {}


def update_devices():
    logger.info("Update info about OrangeFox builds..")
    global DEVICES_STABLE
    global DEVICES_BETA

    ftp = FTP(ftp_url, CONFIG['advanced']['ofox_ftp_user'], CONFIG['advanced']['ofox_ftp_pass'])

    data = ftp.mlsd("OrangeFox-Stable", ["type"])
    for device, facts in data:
        if not facts["type"] == "dir":
            continue

        info_file = []
        ftp.retrlines(f'RETR OrangeFox-Stable/{device}/device_info.txt', info_file.append)

        codename = info_file[0].split(': ')[1]
        fullname = info_file[1].split(': ')[1]
        maintainer = info_file[2].split(': ')[1]

        builds = list(ftp.mlsd("OrangeFox-Stable/" + device, ["type"]))
        builds.sort(key=lambda entry: entry[1]['modify'], reverse=True)
        for build, facts in builds:
            if not facts["type"] == "file":
                continue
            if build == "device_info.txt":
                continue
            last_build = build
            modified = facts['modify']
            break

        DEVICES_STABLE[device] = {
            "codename": codename,
            "fullname": fullname,
            "maintainer": maintainer,
            "ver": last_build,
            "modified": modified
        }

    data = ftp.mlsd("OrangeFox Beta", ["type"])
    for device, facts in data:
        if not facts["type"] == "dir":
            continue

        info_file = []
        ftp.retrlines(f'RETR OrangeFox Beta/{device}/device_info.txt', info_file.append)

        codename = info_file[0].split(': ')[1]
        fullname = info_file[1].split(': ')[1]
        maintainer = info_file[2].split(': ')[1]

        builds = list(ftp.mlsd("OrangeFox Beta/" + device, ["type"]))
        builds.sort(key=lambda entry: entry[1]['modify'], reverse=True)
        for build, facts in builds:
            if not facts["type"] == "file":
                continue
            if build == "device_info.txt":
                continue
            last_build = build
            modified = facts['modify']
            break

        DEVICES_BETA[device] = {
            "codename": codename,
            "fullname": fullname,
            "maintainer": maintainer,
            "ver": last_build,
            "modified": modified
        }
    logger.info("Done!")


# Main
update_devices()
print(DEVICES_STABLE)
print(DEVICES_BETA)


@decorator.command("update", from_users=OWNER_ID)
async def do_update_devices(event):
    update_devices()
    await event.reply("Done")


@decorator.command("list")
@flood_limit_dec("list")
async def list_stable(event):
    if event.chat_id in fox_beta_groups:
        text = "**Beta testing devices:**\n"
        for device in DEVICES_BETA:
            text += "* {} (`{}`)\n".format(
                DEVICES_BETA[device]['fullname'], DEVICES_BETA[device]["codename"])
    elif event.chat_id in fox_groups:
        text = "**Supported devices:**\n"
        for device in DEVICES_STABLE:
            text += "* {} (`{}`)\n".format(
                DEVICES_STABLE[device]['fullname'], DEVICES_STABLE[device]["codename"])
    text += "\nTo get device write `/codename`"
    await event.reply(text)


@decorator.StrictCommand("^[/#](.*)")
async def check(event):
    device_arg = event.pattern_match.group(1).lower()
    if device_arg not in DEVICES_STABLE and device_arg not in DEVICES_BETA:
        return

    if event.chat_id in fox_beta_groups and device_arg in DEVICES_BETA:
        beta_device = DEVICES_BETA[device_arg]
        text = "**" + beta_device['fullname'] + "** (`{}`)".format(beta_device['codename'])
        build = beta_device['ver']
        text += "\nLast beta: `" + build + "`"
        text += "\nDate: `" + beta_device['modified'] + "`"
        if beta_device['maintainer'].isdigit():
            maintainer = await user_link(int(beta_device['maintainer']))
        else:
            maintainer = beta_device['maintainer']
        text += "\nMaintainer: " + maintainer
        link_beta = "https://files.orangefox.website/OrangeFox%20Beta/" + device_arg
        buttons = [[custom.Button.url("Download beta", link_beta + "/" + build),
                    custom.Button.url("All builds", link_beta)]]
    elif event.chat_id in fox_groups and device_arg in DEVICES_STABLE:
        device = DEVICES_STABLE[device_arg]
        text = "**" + device['fullname'] + "** (`{}`)".format(device['codename'])
        build = device['ver']
        text += "\nLast build: `" + build + "`"
        text += "\nDate: `" + device['modified'] + "`"
        if beta_device['maintainer'].isdigit():
            maintainer = await user_link(int(beta_device['maintainer']))
        else:
            maintainer = beta_device['maintainer']
        text += "\nMaintainer: " + maintainer
        link_stable = "https://files.orangefox.website/OrangeFox-Stable/" + device_arg
        buttons = [[custom.Button.url("Download last", link_stable + "/" + build)]]
        link_mirror = "https://sourceforge.net/projects/orangefox/files/"
        buttons += [[custom.Button.url("All builds", link_stable),
                    custom.Button.url("Cloud", link_mirror + device_arg)]]

    await event.reply(text, buttons=buttons)
