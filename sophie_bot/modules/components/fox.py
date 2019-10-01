# Copyright © 2019 MrYacha
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

import hashlib
import io
import re
import pysftp
import subprocess
import os
import time
import datetime
import ujson

from aiogram import types
from aiogram.types.inline_keyboard import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
from aiogram.dispatcher.filters.state import State, StatesGroup

from sophie_bot.modules.main import convert_size
from sophie_bot import CONFIG, decorator, dp, tbot, bot, mongodb, logger


# Constants
FOX_CHATS = [483808054, -1001287179850, -1001280218923, -1001155400138, -1001362128194]
FOX_BETA_CHATS = [-1001280218923, -1001362128194, 483808054]
FOX_DEV_CHAT = -1001155400138
FOX_DOMAIN = 'https://files.orangefox.tech/'

FOX_STABLE_CHANNEL = -1001196811863
FOX_BETA_CHANNEL = -1001429093106

SF_host = 'web.sourceforge.net'
SF_user = 'mryacha'
SF_pass = CONFIG['advanced']['fox_sf_pass']

# FOX_FILES_LOCAL = '/home/yacha/ofoxtest/'
FOX_FILES_LOCAL = '/var/www/fox_files/'


# State
class ReleaseState(StatesGroup):
    sel_build_type = State()
    upload_file = State()
    write_changelog = State()
    write_bugs = State()
    write_build_notes = State()
    releasing = State()


class ChangeDeviceState(StatesGroup):
    create_new_device = State()
    list_info = State()
    change_maintainer = State()
    change_status = State()
    change_def_bugs = State()
    change_def_notes = State()


class AddNewDeviceState(StatesGroup):
    device_full_name = State()


# Callback filters
build_type_cp = CallbackData('fox_build_type', 'build_type')
add_new_device_cb = CallbackData('fox_add_new_device_cb', 'codename')
fox_change_maintainer_cp = CallbackData('fox_change_maintainer_cb', 'codename')
fox_change_status_cp = CallbackData('fox_change_status_cb', 'codename')
fox_change_status_btn_cp = CallbackData('fox_change_status_btn_cp', 'codename', 'status')
fox_change_def_bugs_cp = CallbackData('fox_change_def_bugs_cb', 'codename')
fox_del_def_bugs_cp = CallbackData('fox_del_def_bugs_cb', 'codename')
fox_change_def_notes_cp = CallbackData('fox_change_def_notes_cb', 'codename')
fox_del_def_notes_cp = CallbackData('fox_del_def_notes_cb', 'codename')


# Custom decorators
def dev_chat(func):
    async def wrapped_1(event, *args, **kwargs):

        if hasattr(event, 'message'):
            chat_id = event.message.chat.id
        else:
            chat_id = event.chat.id

        if chat_id == FOX_DEV_CHAT:
            return await func(event, *args, **kwargs)
    return wrapped_1


def ofox_chat(func):
    async def wrapped_1(event, *args, **kwargs):

        if hasattr(event, 'message'):
            chat_id = event.message.chat.id
        else:
            chat_id = event.chat.id

        if chat_id in FOX_CHATS:
            return await func(event, *args, **kwargs)
    return wrapped_1


# Functions
@decorator.register(cmds='release', state='*')
@dev_chat
async def release_new_build(message):
    await ReleaseState.sel_build_type.set()

    text = "<b>Releasing new OrangeFox build</b>"
    text += "\nSelect build type:"
    buttons = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("Stable", callback_data=build_type_cp.new(build_type='stable')),
        InlineKeyboardButton("Beta/RC", callback_data=build_type_cp.new(build_type='beta'))
    )

    buttons.add(
        InlineKeyboardButton("Exit", callback_data='cancel')
    )

    await message.reply(text, reply_markup=buttons)


@dp.callback_query_handler(build_type_cp.filter(), state="*")
async def upload_file_promt(query, callback_data, state, **kwargs):
    await ReleaseState.upload_file.set()
    async with state.proxy() as data:
        data['build_type'] = callback_data['build_type']
    text = f'Great! Please now upload your file here.'
    await query.message.edit_text(text)


@dp.message_handler(state=ReleaseState.upload_file, content_types=types.ContentTypes.DOCUMENT)
async def upload_file(message, state, **kwargs):
    msg = await message.reply("Downloading file...")

    # Parse filename
    file_name = message.document.file_name
    check = re.match(r'OrangeFox\-([^\-]+)\-([^\-]+)\-([^\-]+).zip', file_name)
    if not check:
        await msg.edit_text('Error! File name isnt valid with regex pattern!')
        return
    async with state.proxy() as data:
        data['file_name'] = file_name
        data['build_ver'] = check.group(1)
        data['file_id'] = message.document.file_id
        data['build_date'] = int(time.time())
        codename = check.group(3).lower()
        data['device_codename'] = codename

        if data['build_type'] == 'stable' and not check.group(2).lower() == 'stable':
            await msg.edit_text('Error! Stable builds should be builded with <code>export BUILD_TYPE=Stable</code> tag!')
            return

        # Check device
        device = mongodb.ofox_devices.find_one({'codename': codename})
        if not device:
            await state.finish()
            await message.answer(f"Device not found in database, please write <code>/changedevice {codename}</code>")
            return

        # Check on migrated device
        if 'status' not in device:
            await state.finish()
            await message.answer(f"This device was migrated, please write <code>/changedevice {codename}</code>")
            return

        # Set default builds vars
        if 'default_bugs' in device:
            data['build_bugs'] = device['default_bugs']
        if 'default_notes' in device:
            data['special_notes'] = device['default_notes']

    hash_md5 = hashlib.md5()
    hash_sha256 = hashlib.sha256()
    build_file = io.BytesIO(await tbot.download_media(message.document.file_id, file=bytes))
    for chunk in iter(lambda: build_file.read(4096), b""):
        hash_md5.update(chunk)
        hash_sha256.update(chunk)
    async with state.proxy() as data:
        data['file_md5'] = hash_md5.hexdigest()
        data['file_sha256'] = hash_sha256.hexdigest()
        data['file_size'] = convert_size(build_file.getbuffer().nbytes)

    if not os.path.exists('OrangeFox-temp-builds/'):
        os.makedirs('OrangeFox-temp-builds/')

    with open('OrangeFox-temp-builds/' + file_name, 'wb') as f:
        f.write(build_file.getvalue())
    build_file.close()

    text = 'Done! Please write changelog for this build. HTML markdown supported as well.'
    text += f'\bIf you upload first build - type just "Initial build for {codename}"'
    await ReleaseState.write_changelog.set()
    await msg.edit_text(text)


@dp.callback_query_handler(regexp='fox_changelog_change', state='*')
async def change_changelog(query, state):
    await ReleaseState.write_changelog.set()
    await query.message.edit_text("Please write new changelog")


@dp.callback_query_handler(regexp='fox_add_build_bugs', state='*')
async def change_build_bugs(query, state):
    await ReleaseState.write_bugs.set()
    await query.message.edit_text("Please write build bugs")


@dp.callback_query_handler(regexp='fox_add_build_notes', state='*')
async def change_build_notes(query, state):
    await ReleaseState.write_build_notes.set()
    await query.message.edit_text("Please write special build notes")


@dp.callback_query_handler(regexp='fox_del_build_notes', state='*')
async def del_build_notes(query, state):
    async with state.proxy() as data:
        del data['special_notes']
    await build_process_info(query.message, state, edit=True)


@dp.message_handler(state=ReleaseState.write_changelog)
async def check(message, state, **kwargs):
    changelog_text = message.parse_entities(as_html=True)
    async with state.proxy() as data:
        data['changelog_text'] = changelog_text
    await ReleaseState.releasing.set()
    await build_process_info(message, state, edit=False)


@dp.message_handler(state=ReleaseState.write_bugs)
async def write_bugs_chk(message, state, **kwargs):
    bugs_text = message.parse_entities(as_html=True)
    async with state.proxy() as data:
        data['build_bugs'] = bugs_text
    await ReleaseState.releasing.set()
    await build_process_info(message, state, edit=False)


@dp.message_handler(state=ReleaseState.write_build_notes)
async def write_notes_chk(message, state, **kwargs):
    notes_text = message.parse_entities(as_html=True)
    async with state.proxy() as data:
        data['special_notes'] = notes_text
    await ReleaseState.releasing.set()
    await build_process_info(message, state, edit=False)


async def build_process_info(message, state, edit=True):
    text = '<b>Build info</b>'
    async with state.proxy() as data:
        text += f"\nFile name: <code>{data['file_name']}</code>"
        text += f"\nFile size: <code>{data['file_size']}</code>"
        text += f"\nFile MD5: <code>{data['file_md5']}</code>"
        text += f"\nFile SHA256: <code>{data['file_sha256']}</code>"
        text += "\n"
        text += f"\nDevice codename: <code>{data['device_codename']}</code>"
        text += f"\nBuild type: <code>{data['build_type']}</code>"
        text += f"\nBuild version: <code>{data['build_ver']}</code>"
        if 'special_notes' not in data:
            text += "\nBuild notes: Nothing"
        else:
            text += "\nBuild notes:\n" + data['special_notes']
        if 'build_bugs' not in data:
            text += "\nBuild bugs: Nothing"
        else:
            text += "\nBuild bugs:\n" + data['build_bugs']
        text += "\nBuild changelog:\n" + data['changelog_text']

    buttons = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("📝 Change changelog", callback_data='fox_changelog_change')
    )

    if 'build_bugs' not in data:
        buttons.add(InlineKeyboardButton("🐞 Add build bugs", callback_data='fox_add_build_bugs'))
    else:
        buttons.add(InlineKeyboardButton("🐞 Edit build bugs", callback_data='fox_add_build_bugs'))
    if 'special_notes' not in data:
        buttons.add(InlineKeyboardButton("✏️ Add build notes", callback_data='fox_add_build_notes'))
    else:
        buttons.add(
            InlineKeyboardButton("✏️ Edit build notes", callback_data='fox_add_build_notes'),
            InlineKeyboardButton("❌ Delete build notes", callback_data='fox_del_build_notes')
        )

    buttons.add(
        InlineKeyboardButton("❌ Exit", callback_data='cancel'),
        InlineKeyboardButton("🆗 Release it", callback_data='fox_release_build')
    )

    if edit is True:
        await message.edit_text(text, reply_markup=buttons)
    else:
        await message.reply(text, reply_markup=buttons)


@dp.callback_query_handler(regexp='fox_release_build', state="*")
async def releasing(query, state):
    async with state.proxy() as data:
        file_id = data['file_id']
        codename = data['device_codename']
        build_type = data['build_type']
        file_name = data['file_name']
        build_date = data['build_date']

        device = mongodb.ofox_devices.find_one({'codename': codename})

        build_info_file_txt = "OrangeFox Recovery build info"
        build_info_file_txt += "\nBuild version: " + data['build_ver']
        build_info_file_txt += "\nBuild type: " + data['build_type']
        build_info_file_txt += "\nFile name: " + file_name
        build_info_file_txt += "\nFile size: " + data['file_size']
        build_info_file_txt += "\nFile MD5: " + data['file_md5']
        build_info_file_txt += "\nFile SHA256: " + data['file_sha256']
        if 'special_notes' in data:
            build_info_file_txt += "\nBuild notes:\n" + data['special_notes']
        if 'build_bugs' not in data:
            build_info_file_txt += "\nBuild bugs: Nothing"
        else:
            build_info_file_txt += "\nBuild bugs:\n" + data['build_bugs']
        build_info_file_txt += "\nChangelog:\n" + data['changelog_text']

        if build_type == 'stable':
            files_dir = 'OrangeFox-Stable/'
            release_text = "<b>OrangeFox Recovery</b>"
            channel = FOX_STABLE_CHANNEL
            sdir = 'OrangeFox-Stable/'

        else:
            files_dir = 'OrangeFox-Beta/'
            release_text = "<b>OrangeFox Recovery Beta</b>"
            channel = FOX_BETA_CHANNEL
            sdir = 'OrangeFox-Beta/'

        # OwO

        release_text += f"\n📱 <b>{device['fullname']}</b> (<code>{device['codename']}</code>)"
        release_text += f"\n🔺 Version: <code>{data['build_ver']}</code>"
        release_text += f"\n👨‍🔬 Maintainer: {device['maintainer']}"

        if 'file_md5' in data:
            release_text += f"\n✅ File MD5: <code>{data['file_md5']}</code>"

        release_text += f'\n🗒Changelog:\n' + data['changelog_text']

        new = {
            f'{build_type}_ver': data['build_ver'],
            f'{build_type}_build': file_name,
            f'{build_type}_date': build_date,
            f'{build_type}_md5': data['file_md5'],
            f'{build_type}_sha256': data['file_sha256'],
            f'{build_type}_changelog': data['changelog_text']
        }
        if 'build_bugs' in data:
            new[f'{build_type}_build_bugs'] = data['build_bugs']
            release_text += f'\n🐞 Build Bugs:\n' + data['build_bugs']
        else:
            mongodb.ofox_devices.update_one({'codename': codename}, {'$unset': {f'{build_type}_build_bugs': 1}})
        if 'special_notes' in data:
            new[f'{build_type}_special_notes'] = data['special_notes']
            release_text += '\n📝 Build Notes:\n' + data['special_notes']
        else:
            mongodb.ofox_devices.update_one({'codename': codename}, {'$unset': {f'{build_type}_special_notes': 1}})

        if build_type == 'stable':
            release_text += '\n<a href="https://t.me/OrangeFoxChat">OrangeFox Recovery Support chat</a>'
        else:
            release_text += '\n<a href="https://t.me/joinchat/HNZTNkxOlyslccxryvKeeQ">OrangeFox Beta chat</a>'

    await query.message.edit_text("Releasing. Moving files, uploading to SourceForge and making magic, please wait...")

    # Copy file to stable dir
    if not os.path.exists(FOX_FILES_LOCAL + sdir):
        os.makedirs(FOX_FILES_LOCAL + sdir)

    path = FOX_FILES_LOCAL + sdir + codename + '/'
    if not os.path.exists(path):
        os.makedirs(path)

    local_file = path + file_name

    subprocess.call(f'mv OrangeFox-temp-builds/{file_name} {local_file}', shell=True)
    with open(local_file[:-3] + 'txt', 'w') as f:
        f.write(build_info_file_txt)

    sf = False

    if build_type == 'stable':
        # SourceForge
        try:
            cnopts = pysftp.CnOpts()
            cnopts.hostkeys = None
            with pysftp.Connection(host=SF_host, username=SF_user, password=SF_pass, cnopts=cnopts) as sftp:
                with sftp.cd('/home/frs/project/orangefox'):
                    if not sftp.isdir(codename):
                        sftp.mkdir(codename)
                    with sftp.cd('/home/frs/project/orangefox/' + codename):
                        sftp.put(local_file)
            new[f'{build_type}_sf'] = True
            sf = True
        except Exception as err:
            await query.message.answer("Can't connect to SF, skipping!")
            new[f'{build_type}_sf'] = False
            sf = False
            logger.error(err)

    mongodb.ofox_devices.update_one({'codename': codename}, {'$set': new})
    mongodb.ofox_devices.update_one({'codename': codename}, {'$unset': {f'{build_type}_migrated': 1}})

    build_json_file()

    buttons = InlineKeyboardMarkup().add(
        InlineKeyboardButton("⬇️ Direct download", url=FOX_DOMAIN + files_dir + codename + '/' + file_name)
    )

    if sf is True:
        sf_url = 'https://sourceforge.net/projects/orangefox/files/' + codename + '/' + file_name
        buttons.add(InlineKeyboardButton("☁️ Cloud", url=sf_url))

    # Send sticker
    await bot.send_document(
        channel,
        "CAADAgADAwAD6rr0F491IJH_DoTNFgQ"
    )

    # Send release
    await bot.send_document(
        channel,
        file_id,
        caption=release_text,
        reply_markup=buttons
    )

    await query.message.edit_text("All done!")
    await state.finish()

# Change device


@decorator.register(cmds='changedevice')
@dev_chat
async def change_device_info_cmd(message):
    device_codename = message.get_args().lower()
    device = mongodb.ofox_devices.find_one({'codename': device_codename})
    if not device:
        await ChangeDeviceState.create_new_device.set()
        text = f"Device <code>{device_codename}</code> not found in database, would you like to create it?"
        buttons = InlineKeyboardMarkup(row_width=2).add(
            InlineKeyboardButton("Yes", callback_data=add_new_device_cb.new(codename=device_codename)),
            InlineKeyboardButton("No", callback_data='cancel'),
        )
        await message.answer(text, reply_markup=buttons)
        return
    if 'status' not in device:
        await ChangeDeviceState.list_info.set()
        text = f"Device <code>{device_codename}</code> migrated, please press 'OK'"
        buttons = InlineKeyboardMarkup().add(
            InlineKeyboardButton("OK", callback_data=fox_change_status_cp.new(codename=device_codename)),
        )
        await message.answer(text, reply_markup=buttons)
        return
    await change_device_info(message, device)


@dp.callback_query_handler(add_new_device_cb.filter(), state="*")
async def crt_dev_full_name(query, callback_data, state):
    await AddNewDeviceState.device_full_name.set()
    async with state.proxy() as data:
        data['codename'] = callback_data['codename']
    await query.message.edit_text("Please write device full name, for example: Xiaomi Redmi Note 5 (Pro)")


@dp.message_handler(state=AddNewDeviceState.device_full_name)
async def crt_device(message, state, **kwargs):
    async with state.proxy() as data:
        device_codename = data['codename']
    device_full_name = message.text

    new = {
        'codename': device_codename,
        'fullname': device_full_name,
        'maintainer': message.from_user.first_name,
        'status': "Maintained"
    }

    mongodb.ofox_devices.insert_one(new)
    await change_device_info(message, new)


async def change_device_info(message, device, edit=False):
    await ChangeDeviceState.list_info.set()
    codename = device['codename']
    text = "Device name: " + device['fullname']
    text += "\nCodename: " + codename
    text += "\nMaintainer: " + device['maintainer']
    text += "\nStatus: " + device['status']
    if 'default_bugs' in device:
        text += "\nDefault builds bugs:\n" + device['default_bugs']
    if 'default_notes' in device:
        text += "\nDefault builds notes:\n" + device['default_notes']

    buttons = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("Change maintainer", callback_data=fox_change_maintainer_cp.new(codename=codename)),
        InlineKeyboardButton("Change development status", callback_data=fox_change_status_cp.new(codename=codename))
    )

    if 'default_bugs' not in device:
        buttons.add(InlineKeyboardButton("Add default bugs", callback_data=fox_change_def_bugs_cp.new(codename=codename)))
    else:
        buttons.add(
            InlineKeyboardButton("Edit default bugs", callback_data=fox_change_def_bugs_cp.new(codename=codename)),
            InlineKeyboardButton("Delete default bugs", callback_data=fox_del_def_bugs_cp.new(codename=codename))
        )

    if 'default_notes' not in device:
        buttons.add(InlineKeyboardButton("Add default notes", callback_data=fox_change_def_notes_cp.new(codename=codename)))
    else:
        buttons.add(
            InlineKeyboardButton("Edit default notes", callback_data=fox_change_def_notes_cp.new(codename=codename)),
            InlineKeyboardButton("Delete default notes", callback_data=fox_del_def_notes_cp.new(codename=codename))
        )

    buttons.add(
        InlineKeyboardButton("Done", callback_data='cancel')
    )

    if edit is True:
        await message.edit_text(text, reply_markup=buttons)
    else:
        await message.reply(text, reply_markup=buttons)


@dp.callback_query_handler(fox_change_maintainer_cp.filter(), state="*")
async def change_device_maintainer(query, callback_data, state):
    async with state.proxy() as data:
        data['codename'] = callback_data['codename']
    await ChangeDeviceState.change_maintainer.set()
    await query.message.edit_text("Write new maintainer name")


@dp.message_handler(state=ChangeDeviceState.change_maintainer)
async def change_device_maintainer_done(message, state, **kwargs):
    async with state.proxy() as data:
        codename = data['codename']
    mongodb.ofox_devices.update_one({'codename': codename}, {'$set': {'maintainer': message.text}})
    device = mongodb.ofox_devices.find_one({'codename': codename})
    await change_device_info(message, device, edit=False)


@dp.callback_query_handler(fox_change_status_cp.filter(), state="*")
async def change_device_status(query, callback_data, state):
    codename = callback_data['codename']
    await ChangeDeviceState.change_status.set()

    buttons = InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton("Maintained", callback_data=fox_change_status_btn_cp.new(
            codename=codename, status=1)),
        InlineKeyboardButton("Maintained without device on hands", callback_data=fox_change_status_btn_cp.new(
            codename=codename, status=2)),
        InlineKeyboardButton("Testing only", callback_data=fox_change_status_btn_cp.new(
            codename=codename, status=3)),
        InlineKeyboardButton("Unmaintained", callback_data=fox_change_status_btn_cp.new(
            codename=codename, status=4)),
    )

    await query.message.edit_text("Select device status:", reply_markup=buttons)


@dp.callback_query_handler(fox_change_status_btn_cp.filter(), state="*")
async def change_device_status_btn(query, callback_data, state):
    codename = callback_data['codename']
    num = int(callback_data['status'])

    if num == 1:
        status = "Maintained"
    elif num == 2:
        status = "Maintained without device on hands"
    elif num == 3:
        status = "Testing only"
    elif num == 4:
        status = "Unmaintained"

    mongodb.ofox_devices.update_one({'codename': codename}, {'$set': {'status': status}})
    device = mongodb.ofox_devices.find_one({'codename': codename})
    await change_device_info(query.message, device, edit=True)


@dp.callback_query_handler(fox_change_def_bugs_cp.filter(), state="*")
async def change_default_bugs(query, callback_data, state):
    async with state.proxy() as data:
        data['codename'] = callback_data['codename']
    await ChangeDeviceState.change_def_bugs.set()
    await query.message.edit_text("Write known bugs here, they will be added in all build by default")


@dp.message_handler(state=ChangeDeviceState.change_def_bugs)
async def change_default_bugs_done(message, state, **kwargs):
    async with state.proxy() as data:
        codename = data['codename']
    mongodb.ofox_devices.update_one({'codename': codename}, {'$set': {'default_bugs': message.text}})
    device = mongodb.ofox_devices.find_one({'codename': codename})
    await change_device_info(message, device, edit=False)


@dp.callback_query_handler(fox_del_def_bugs_cp.filter(), state="*")
async def del_default_bugs(query, callback_data, state):
    codename = callback_data['codename']
    mongodb.ofox_devices.update_one({'codename': codename}, {'$unset': {'default_bugs': 1}})
    device = mongodb.ofox_devices.find_one({'codename': codename})
    await change_device_info(query.message, device, edit=True)


@dp.callback_query_handler(fox_change_def_notes_cp.filter(), state="*")
async def change_default_notes(query, callback_data, state):
    async with state.proxy() as data:
        data['codename'] = callback_data['codename']
    await ChangeDeviceState.change_def_notes.set()
    await query.message.edit_text("Write default notes here. HTML markdown supported as well.")


@dp.message_handler(state=ChangeDeviceState.change_def_notes)
async def change_default_notes_done(message, state, **kwargs):
    async with state.proxy() as data:
        codename = data['codename']
    mongodb.ofox_devices.update_one({'codename': codename}, {'$set': {'default_notes': message.parse_entities(as_html=True)}})
    device = mongodb.ofox_devices.find_one({'codename': codename})
    await change_device_info(message, device, edit=False)


@dp.callback_query_handler(fox_del_def_notes_cp.filter(), state="*")
async def del_default_notes(query, callback_data, state):
    codename = callback_data['codename']
    mongodb.ofox_devices.update_one({'codename': codename}, {'$unset': {'default_notes': 1}})
    device = mongodb.ofox_devices.find_one({'codename': codename})
    await change_device_info(query.message, device, edit=True)


@decorator.register(cmds='list')
@ofox_chat
async def list_all_device(message, **args):
    chat_id = message.chat.id
    if chat_id == FOX_DEV_CHAT:
        text = "<b>All devices list:</b>"
        search = {}
    elif chat_id in FOX_BETA_CHATS:
        text = "<b>Beta devices list:</b>"
        search = {'beta_build': {'$exists': True}}
    else:
        text = "<b>Stable devices list:</b>"
        search = {'stable_build': {'$exists': True}}
    all_devices = mongodb.ofox_devices.find(search)
    for device in sorted(all_devices, key=lambda x: x['fullname'], reverse=False):
        text += f"\n{device['fullname']} (<code>{device['codename']}</code>)"

    text += "\n\n<b>To get device write</b> <code>/codename</code>"

    msg = await message.reply(text)

    # Del prev msg code
    old_msg = mongodb.old_fox_msgs.find_one({'chat_id': chat_id})
    new = {
        'chat_id': chat_id,
        'last_msg': msg.message_id,
        'last_user_msg': message.message_id
    }
    if not old_msg:
        mongodb.old_fox_msgs.insert_one(new)
        return
    owo = []
    if 'last_msg' in old_msg:
        owo.append(old_msg['last_msg'])
    if 'last_user_msg' in old_msg:
        owo.append(old_msg['last_user_msg'])
    try:
        await tbot.delete_messages(chat_id, owo)
    except Exception:
        pass

    mongodb.old_fox_msgs.update_one({'_id': old_msg['_id']}, {'$set': new}, upsert=True)


@dp.message_handler(regexp=r"^[!/#](.*)")
@ofox_chat
async def get_build_info(message, **args):
    codename = message.text.split('@rSophieBot')[0][1:].lower()
    device = mongodb.ofox_devices.find_one({'codename': codename})
    if not device:
        return
    chat_id = message.chat.id
    chat_type = 'stable'
    files_dir = 'OrangeFox-Stable/'
    text = ''
    if chat_id in FOX_BETA_CHATS:
        text = '<b>OrangeFox Recovery Beta</b>\n'
        chat_type = 'beta'
        files_dir = 'OrangeFox-Beta/'

    if f'{chat_type}_build' not in device:
        text = f'This device not support {chat_type} builds, check '
        if chat_type == 'stable':
            text += '<a href="https://t.me/joinchat/HNZTNkxOlyslccxryvKeeQ">OrangeFox Beta chat</a>'
        else:
            text += '<a href="https://t.me/OrangeFoxChat">OrangeFox Main chat</a>'
        await message.reply(text)
        return

    last_build = device[chat_type + "_build"]

    text += f"📱 <b>{device['fullname']}</b> (<code>{device['codename']}</code>)"
    text += f'\n📄 Last {chat_type} build: <code>{last_build}</code>'
    date_str = datetime.datetime.fromtimestamp(device[f'{chat_type}_date']).strftime('%a %b %d %H:%M %Y')
    text += f'\n📅 Date: <code>{date_str}</code>'
    text += f"\n👨‍🔬 Maintainer: {device['maintainer']}"

    if 'status' in device:
        text += f", status: <code>{device['status']}</code>"

    if f'{chat_type}_md5' in device:
        text += f"\n✅ File MD5: <code>{device[chat_type + '_md5']}</code>"

    if f'{chat_type}_build_bugs' in device:
        text += f'\n🐞 Build Bugs:\n' + device[chat_type + '_build_bugs']

    if f'{chat_type}_special_notes' in device:
        text += f'\n📝 Build Notes:\n' + device[chat_type + '_special_notes']

    if os.path.exists(FOX_FILES_LOCAL + files_dir + codename + '/' + last_build[:-3] + 'txt'):
        text += f"\n<a href=\"{FOX_DOMAIN + files_dir + codename + '/' + last_build[:-3] + 'txt'}\">🗒 View changelog and more info</a>"

    buttons = InlineKeyboardMarkup().add(
        InlineKeyboardButton("⬇️ Download this build", url=FOX_DOMAIN + files_dir + codename + '/' + last_build)
    )

    if f'{chat_type}_sf' in device and device[f'{chat_type}_sf'] is True:
        print('owo')
        buttons.add(InlineKeyboardButton("🗄️ All builds", url=FOX_DOMAIN + files_dir))
        sf_url = 'https://sourceforge.net/projects/orangefox/files/' + codename + '/' + last_build
        buttons.insert(InlineKeyboardButton("☁️ Cloud", url=sf_url))
    else:
        buttons.insert(InlineKeyboardButton("🗄️ All builds", url=FOX_DOMAIN + files_dir))

    msg = await message.reply(text, reply_markup=buttons, disable_web_page_preview=True)

    # Del prev msg code
    old_msg = mongodb.old_fox_msgs.find_one({'chat_id': chat_id})
    new = {
        'chat_id': chat_id,
        'last_msg': msg.message_id,
        'last_user_msg': message.message_id
    }
    if not old_msg:
        mongodb.old_fox_msgs.insert_one(new)
        return
    owo = []
    if 'last_msg' in old_msg:
        owo.append(old_msg['last_msg'])
    if 'last_user_msg' in old_msg:
        owo.append(old_msg['last_user_msg'])
    try:
        await tbot.delete_messages(chat_id, owo)
    except Exception:
        pass

    mongodb.old_fox_msgs.update_one({'_id': old_msg['_id']}, {'$set': new}, upsert=True)


def build_json_file():
    new = {}
    all_devices = mongodb.ofox_devices.find()
    for device in all_devices:
        new[device['codename']] = device
        del new[device['codename']]['_id']

    if not os.path.exists(FOX_FILES_LOCAL + 'Other/'):
        os.makedirs(FOX_FILES_LOCAL + 'Other/')

    with open(FOX_FILES_LOCAL + 'Other/update_v2.json', 'w') as f:
        ujson.dump(new, f, indent=1)
