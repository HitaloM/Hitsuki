import random

from requests import post

from telethon.errors import BadRequestError, ChatNotModifiedError
from telethon.tl.custom import Button
from telethon.tl.functions.channels import EditAdminRequest
from telethon.tl.types import ChatAdminRights

import sophie_bot.modules.helper_func.bot_rights as bot_rights
from sophie_bot import OWNER_ID, SUDO, BOT_USERNAME, tbot, decorator, mongodb
from sophie_bot.modules.disable import disablable_dec
from sophie_bot.modules.language import get_string, get_strings_dec
from sophie_bot.modules.users import (get_user, user_admin_dec,
                                      user_link, aio_get_user, user_link_html, is_user_admin)


@decorator.command('allcommands')
async def all_commands_list(message):
    txt = ""
    for cmd in decorator.REGISTRED_COMMANDS:
        txt += "* /" + cmd + "\n"
    await message.reply(txt)


@decorator.command("id")
@disablable_dec("id")
@get_strings_dec('misc')
async def get_id(message, strings):
    user, txt = await aio_get_user(message, allow_self=True)
    if not user:
        return
    text = strings["your_id"].format(message.from_user.id)
    text += strings["chat_id"].format(message.chat.id)

    if not user['user_id'] == message.from_user.id:
        userl = await user_link(user['user_id'])
        text += strings["user_id"].format(userl, user['user_id'])

    if "reply_to_message" in message:
        userl = await user_link_html(message.reply_to_message.from_user.id)
        text += strings["user_id"].format(userl, message.reply_to_message.from_user.id)
        if "forward_from" in message.reply_to_message and not \
           message.reply_to_message.forward_from.id == message.reply_to_message.from_user.id:
            userl = await user_link_html(message.reply_to_message.forward_from.id)
            text += strings["user_id"].format(userl, message.reply_to_message.from_user.id)

    await message.reply(text)


@decorator.t_command("pin", arg=True)
@user_admin_dec
@bot_rights.pin_messages()
@get_strings_dec('misc')
async def pinMessage(event, strings):
    tagged_message = await event.get_reply_message()
    if not tagged_message:
        await event.reply(get_string('misc', 'no_reply_msg', event.chat_id))
        return
    msg_2_pin = tagged_message.id
    chk = event.pattern_match.group(1)
    args = chk.lower()
    tru_txt = ['loud', 'notify']
    chat = event.chat_id
    if args in tru_txt:
        notify = True
    else:
        notify = False
    try:
        await tbot.pin_message(chat, msg_2_pin, notify=notify)
    except ChatNotModifiedError:
        await event.reply(strings['chat_not_modified_pin'])
        return


@decorator.t_command("runs")
@get_strings_dec("RUNS", mas_name="RANDOM_STRINGS")
async def runs(event, strings):
    await event.reply(strings[random.choice(list(strings))])


@decorator.t_command("unpin")
@user_admin_dec
@bot_rights.pin_messages()
@get_strings_dec('misc')
async def unpin_message(event, strings):
    try:
        await tbot.pin_message(event.chat_id, None)
    except ChatNotModifiedError:
        await event.reply(strings['chat_not_modified_unpin'])
        return


@decorator.t_command("promote", arg=True)
@user_admin_dec
@bot_rights.add_admins()
async def promote(event):
    user = await get_user(event)
    if user:
        pass
    else:
        return

    new_rights = ChatAdminRights(
        add_admins=True,
        invite_users=True,
        change_info=True,
        ban_users=True,
        delete_messages=True,
        pin_messages=True
    )

    try:
        await event.client(
            EditAdminRequest(
                event.chat_id,
                user['user_id'],
                new_rights
            )
        )
        await event.reply(get_string('misc', 'promote_success', event.chat_id))

    except BadRequestError:  # TODO(Better exception)
        await event.reply(get_string('misc', 'promote_failed', event.chat_id))
        return


@decorator.t_command("demote")
@user_admin_dec
@bot_rights.add_admins()
async def demote(event):
    # Admin right check

    user = await get_user(event)
    if user:
        pass
    else:
        return

    bot_id = (await tbot.get_me()).id
    if bot_id == user['user_id']:
        return

    # New rights after demotion
    newrights = ChatAdminRights(
        add_admins=None,
        invite_users=None,
        change_info=None,
        ban_users=None,
        delete_messages=None,
        pin_messages=None
    )
    # Edit Admin Permission
    try:
        await event.client(
            EditAdminRequest(
                event.chat_id,
                user['user_id'],
                newrights
            )
        )

    # If we catch BadRequestError from Telethon
    # Assume we don't have permission to demote
    except BadRequestError:
        await event.reply(get_string('misc', 'demote_failed', event.chat_id))
        return
    await event.reply(get_string('misc', 'demote_success', event.chat_id))


@decorator.t_command('help')
@get_strings_dec('misc')
async def help(event, strings):
    if event.chat_id != event.from_id:
        buttons = [
            [Button.url(strings['help_btn'], url='https://t.me/{}?start=help'.format(BOT_USERNAME))]
        ]
        text = strings['help_txt']
        await event.reply(text, buttons=buttons)


@decorator.command('paste')
@get_strings_dec('misc')
async def paste_deldog(message, strings, **kwargs):
    DOGBIN_URL = "https://del.dog/"
    dogbin_final_url = None
    to_paste = None

    if 'reply_to_message' in message:
        to_paste = message.reply_to_message.text
    else:
        to_paste = message.text.split(' ', 1)[1]

    if not to_paste:
        await message.reply(strings['paste_no_text'])
        return

    resp = post(DOGBIN_URL + "documents", data=to_paste.encode('utf-8'))

    if resp.status_code == 200:
        response = resp.json()
        key = response['key']
        dogbin_final_url = DOGBIN_URL + key

        if response['isUrl']:
            full_url = "{}v/{}".format(DOGBIN_URL, key)
            reply_text = (strings["paste_success_extra"].format(dogbin_final_url, full_url))
        else:
            reply_text = (strings["paste_success"].format(dogbin_final_url))
    else:
        reply_text = (strings["paste_fail"])

    await message.reply(reply_text, disable_web_page_preview=True)


@decorator.command("info")
@get_strings_dec("misc")
async def user_info(message, strings, **kwargs):
    user, txt = await aio_get_user(message, allow_self=True)
    if not user:
        return

    chat_id = message.chat.id
    from_id = message.from_user.id

    text = strings["user_info"]
    text += strings["info_id"].format(id=user['user_id'])

    text += strings["info_first"].format(first_name=str(user['first_name']))

    if user['last_name'] is not None:
        text += strings["info_last"].format(last_name=str(user['last_name']))

    if user['username'] is not None:
        text += strings["info_username"].format(username="@" + str(user['username']))

    text += strings['info_link'].format(user_link=str(await user_link_html(user['user_id'])))

    text += '\n'

    if await is_user_admin(chat_id, user['user_id']) is True:
        text += strings['info_admeme']

    text += strings['info_saw'].format(num=len(user['chats']))

    if user['user_id'] == OWNER_ID:
        text += strings["father"]
    elif user['user_id'] in SUDO:
        text += strings['sudo_crown']
    else:
        text += "\n"

        fed = mongodb.fed_groups.find_one({'chat_id': chat_id})
        if fed:
            fbanned = mongodb.fbanned_users.find_one({'user': from_id, 'fed_id': fed['fed_id']})
            text += strings['info_fbanned']
            if fbanned:
                text += strings['gbanned_yes']
                text += strings["gbanned_reason"].format(reason=fbanned['reason'])
            else:
                text += strings['no']
        text += strings["gbanned"]

        check = mongodb.blacklisted_users.find_one({'user': user['user_id']})
        if check:
            text += strings['gbanned_yes']
            text += strings["gbanned_date"].format(data=check['date'])
            text += strings["gbanned_reason"].format(reason=check['reason'])
        else:
            text += strings['no']

    await message.reply(text)
