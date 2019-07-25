from ftplib import FTP
from time import gmtime, strftime
import ujson
import os

from telethon import custom

from sophie_bot import CONFIG, decorator, logger, tbot, mongodb
from sophie_bot.modules.helper_func.flood import flood_limit_dec

ftp_url = "ftp.orangefox.website"
fox_groups = [483808054, -1001287179850, -1001280218923, -1001155400138, -1001362128194]
fox_beta_groups = [-1001280218923, -1001362128194]
fox_dev_chats = [-1001155400138, 483808054]

BETA_CHANNEL = -1001429093106
STABLE_CHANNEL = -1001196811863

global DEVICES_STABLE
global DEVICES_BETA

DEVICES_STABLE = {}
DEVICES_BETA = {}

NEW_BETA_TEXT = """🦊 **OrangeFox Beta**
`{ver}`

📱 {fullname} ({codename})
📅 Date: `{modified}`

👤 Maintainer: {maintainer}
{msg}
ℹ️ ChangeLog:
{changelog}

💬 **Beta testing group:** [join](https://t.me/joinchat/HNZTNha1iBzpX-_33EdEsg)"""

NEW_STABLE_TEXT = """🦊 **OrangeFox R10 Stable**
`{ver}`

📱 {fullname} ({codename})
📅 Date: `{modified}`

👤 Maintainer: {maintainer}
{msg}
ℹ️ ChangeLog:
{changelog}

💬 **OrangeFox chat:** [join](https://t.me/joinchat/HNZTNky4zkpWc7na_-Beow)"""


@decorator.t_command("update")
async def update_devices(event):
    if event.chat_id not in fox_dev_chats:
        return

    logger.info("Update info about OrangeFox builds..")
    global DEVICES_STABLE
    global DEVICES_BETA

    DEVICES_STABLE = {}
    DEVICES_BETA = {}
    if os.path.exists("update.json"):
        f = open("update.json", "r")
        jfile = ujson.load(f)
        old_beta = jfile['beta']
        old_stable = jfile['stable']
    else:
        await event.reply("update.json didn't found in the bot directory, regenerating...")
        old_beta = []
        old_stable = []

    released_stable = ""
    released_beta = ""

    ftp = FTP(ftp_url, CONFIG['advanced']['ofox_ftp_user'], CONFIG['advanced']['ofox_ftp_pass'])

    Omsg = await event.reply("Updating Stable devices..")
    data = ftp.mlsd("OrangeFox-Stable", ["type"])
    for device, facts in data:
        if not facts["type"] == "dir":
            continue

        info_file = []
        ftp.retrlines(f'RETR OrangeFox-Stable/{device}/device_info.txt', info_file.append)

        codename = info_file[0].split(': ')[1].lower()
        fullname = info_file[1].split(': ')[1]
        maintainer = info_file[2].split(': ')[1]
        msg = ""
        if len(info_file) >= 4:
            msg = info_file[3].split(': ')[1]

        builds = list(ftp.mlsd("OrangeFox-Stable/" + device, ["type"]))
        builds.sort(key=lambda entry: entry[1]['modify'], reverse=True)
        readme = None
        done = 0
        for build, facts in builds:
            logger.debug(build)
            if not facts["type"] == "file":
                continue
            elif build == "README.md":
                readme = "README.md"
                continue

            ext = os.path.splitext(build)[1]
            if ext == '.zip' and done == 0:
                last_build = build
                modified = facts['modify']
                done = 1

        mm = list(ftp.mlsd(f"OrangeFox-Stable/{device}/{last_build[:-4]}.txt"))
        if mm:
            handle = open("changelog.txt", 'wb')
            ftp.retrbinary(f'RETR OrangeFox-Stable/{device}/{last_build[:-4]}.txt', handle.write)
            handle.close()
            handle = open("changelog.txt", 'rU')
            changelog = handle.read()
            handle.close()
        else:
            changelog = None

        DEVICES_STABLE[codename] = {
            "codename": codename,
            "fullname": fullname,
            "maintainer": maintainer,
            "ver": last_build,
            "modified": modified,
            "readme": readme,
            "msg": msg,
            "changelog": changelog
        }

        # Check on update
        if codename not in old_stable or int(modified) > int(old_stable[codename]['modified']):
            released_stable += f"{codename} "
            logger.info(f'Stable - new update of {codename} detected.')
            link = 'https://files.orangefox.website/OrangeFox-Stable/' + device + "/" + last_build

            await tbot.send_message(
                STABLE_CHANNEL,
                NEW_STABLE_TEXT.format_map(DEVICES_STABLE[codename]),
                buttons=[[custom.Button.url(
                    "⬇️ Download this build", link
                )]],
                link_preview=False
            )

    await Omsg.edit("Updating Beta devices..")
    data = ftp.mlsd("OrangeFox-Beta", ["type"])
    for device, facts in data:
        if not facts["type"] == "dir":
            continue

        info_file = []
        ftp.retrlines(f'RETR OrangeFox-Beta/{device}/device_info.txt', info_file.append)

        codename = info_file[0].split(': ')[1].lower()
        fullname = info_file[1].split(': ')[1]
        maintainer = info_file[2].split(': ')[1]
        msg = None
        if len(info_file) >= 4:
            msg = info_file[3].split(': ')[1]

        builds = list(ftp.mlsd("OrangeFox-Beta/" + device, ["type"]))
        builds.sort(key=lambda entry: entry[1]['modify'], reverse=True)
        readme = None
        done = 0
        for build, facts in builds:
            logger.debug(build)
            if not facts["type"] == "file":
                continue
            elif build == "README.md":
                readme = "README.md"
                continue

            ext = os.path.splitext(build)[1]
            if ext == '.zip' and done == 0:
                last_build = build
                modified = facts['modify']
                done = 1

        mm = list(ftp.mlsd(f"OrangeFox-Beta/{device}/{last_build[:-4]}.txt"))
        if mm:
            handle = open("changelog.txt", 'wb')
            ftp.retrbinary(f'RETR OrangeFox-Beta/{device}/{last_build[:-4]}.txt', handle.write)
            handle.close()
            handle = open("changelog.txt", 'rU')
            changelog = handle.read()
            handle.close()
        else:
            changelog = None

        DEVICES_BETA[codename] = {
            "codename": codename,
            "fullname": fullname,
            "maintainer": maintainer,
            "ver": last_build,
            "modified": modified,
            "readme": readme,
            "msg": msg,
            "changelog": changelog
        }

        # Check on update
        if codename not in old_beta or int(modified) > int(old_beta[codename]['modified']):
            released_beta += f"{codename} "
            logger.info(f'BETA - new update of {codename} detected.')
            link = 'https://files.orangefox.website/OrangeFox-Beta/' + device + "/" + last_build

            await tbot.send_message(
                BETA_CHANNEL,
                NEW_BETA_TEXT.format_map(DEVICES_BETA[codename]),
                buttons=[[custom.Button.url(
                    "⬇️ Download this Beta", link
                )]],
                link_preview=False
            )

    date = strftime("%Y-%m-%d %H:%M:%S", gmtime())

    JSON_FILE = {
        'stable': DEVICES_STABLE,
        'beta': DEVICES_BETA,
        'json_file_info': {"ver": 4, "generated_date": date}
    }
    f = open("update.json", "w+")

    ujson.dump(JSON_FILE, f, indent=1)
    f.close()
    with open('update.json', 'rb') as f:
        ftp.storbinary('STOR %s' % 'Others/update.json', f)

    ftp.quit()

    text = "Done!\n"
    if released_stable:
        text += f"Stable updates released:\n{released_stable}\n"
    if released_beta:
        text += f"Beta updates released:\n{released_beta}"

    await Omsg.edit(text)

    logger.info(text)


# Main
if os.path.exists("update.json"):
    f = open("update.json", "r")
    jfile = ujson.load(f)
    DEVICES_STABLE = jfile['stable']
    DEVICES_BETA = jfile['beta']

print(DEVICES_STABLE)
print(DEVICES_BETA)


@decorator.t_command("list")
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
    msg = await event.reply(text)
    old_msg = mongodb.old_fox_msgs.find_one({'chat_id': event.chat_id})
    new = {
        'chat_id': event.chat_id,
        'last_msg': msg.id
    }
    if not old_msg:
        mongodb.old_fox_msgs.insert_one(new)
        return
    owo = []
    owo.append(old_msg['last_msg'])
    await event.client.delete_messages(event.chat_id, owo)

    mongodb.old_fox_msgs.update_one({'_id': old_msg['_id']}, {'$set': new}, upsert=True)


@decorator.StrictCommand("^[!/#](.*)")
async def check(event):
    device_arg = event.pattern_match.group(1).lower()
    text = None

    if event.chat_id in fox_beta_groups:
        for device in DEVICES_BETA:
            if device_arg.lower() == device.lower():
                beta_device = DEVICES_BETA[device_arg]
                text = "📱 **" + beta_device['fullname'] + "** (`{}`)".format(
                    beta_device['codename'])
                build = beta_device['ver']
                text += "\n📁 Last beta: `" + build + "`"
                text += "\n📅 Date: `" + beta_device['modified'] + "`"
                maintainer = beta_device['maintainer']
                text += "\n👨‍🔬 Maintainer: " + maintainer
                link_beta = "https://files.orangefox.website/OrangeFox-Beta/" + device_arg
                buttons = []
                if beta_device['msg']:
                    text += "\n🗒️ Notes:\n" + beta_device['msg'].replace('\\n', "\n")
                if beta_device['readme']:
                    buttons.append([custom.Button.url(
                        f"📄 Readme file ({beta_device['readme']})", link_beta)])
                buttons.append([custom.Button.url("⬇️ Download beta", link_beta + "/" + build),
                               custom.Button.url("🗄️ All builds", link_beta)])

    elif event.chat_id in fox_groups:
        for device in DEVICES_STABLE:
            if device_arg.lower() == device.lower():
                device = DEVICES_STABLE[device_arg]
                text = "📱 **" + device['fullname'] + "** (`{}`)".format(device['codename'])
                build = device['ver']
                text += "\n📁 Last build: `" + build + "`"
                text += "\n📅 Date: `" + device['modified'] + "`"
                maintainer = device['maintainer']
                text += "\n👨‍🔬 Maintainer: " + maintainer
                link_stable = "https://files.orangefox.website/OrangeFox-Stable/" + device_arg
                buttons = [[custom.Button.url("Download last", link_stable + "/" + build)]]
                link_mirror = "https://sourceforge.net/projects/orangefox/files/"
                buttons = []
                if device['msg']:
                    text += "\n🗒️ Notes:\n" + device['msg'].replace('\\n', "\n")
                buttons.append([custom.Button.url("⬇️ Download last", link_stable + "/" + build)])
                if device['readme']:
                    buttons.append([custom.Button.url(f"📄 Readme file ({device['readme']})",
                                   link_stable)])
                buttons.append([custom.Button.url("🗄️ All builds", link_stable),
                               custom.Button.url("☁️ Cloud", link_mirror + device_arg)])
    if text:
        msg = await event.reply(text, buttons=buttons)

        old_msg = mongodb.old_fox_msgs.find_one({'chat_id': event.chat_id})

        new = {
            'chat_id': event.chat_id,
            'last_msg': msg.id
        }

        if not old_msg:
            mongodb.old_fox_msgs.insert_one(new)
            return

        owo = []
        owo.append(old_msg['last_msg'])
        await event.client.delete_messages(event.chat_id, owo)


        mongodb.old_fox_msgs.update_one({'_id': old_msg['_id']}, {'$set': new}, upsert=True)
