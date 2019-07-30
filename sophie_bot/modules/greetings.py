import re
import time

from telethon.tl.custom import Button

from telethon.errors.rpcerrorlist import MessageDeleteForbiddenError
from aiogram.utils.exceptions import CantDemoteChatCreator

from aiogram import types

from aiogram.types.inline_keyboard import InlineKeyboardMarkup, InlineKeyboardButton
from sophie_bot import tbot, decorator, mongodb, dp
from sophie_bot.modules.bans import mute_user, unmute_user
from sophie_bot.modules.connections import connection
from sophie_bot.modules.language import get_strings_dec
from sophie_bot.modules.notes import send_note
from sophie_bot.modules.users import user_admin_dec, user_link_html


async def do_welcomesecurity(message, strings, from_id, chat_id):
    welcome_security = mongodb.welcome_security.find_one({'chat_id': chat_id})
    if welcome_security and welcome_security['security'] == 'soft':
        buttons = InlineKeyboardMarkup().add(InlineKeyboardButton(
            strings['clik2tlk_btn'], callback_data='wlcm_{}_{}'.format(from_id, chat_id)
        ))
        time_val = int(time.time() + 60 * 60)  # Mute 1 hour
        await mute_user(message, int(from_id), chat_id, time_val)
        text = strings['wlcm_sec'].format(mention=await user_link_html(from_id))
        await message.reply(text, reply_markup=buttons)

    elif welcome_security and welcome_security['security'] == 'hard':
        buttons = [
            [Button.inline(strings['clik2tlk_btn'], 'wlcm_{}_{}'.format(from_id, chat_id))]
        ]
        try:
            await mute_user(message, int(from_id), chat_id, None)
        except CantDemoteChatCreator:
            return

        text = strings['wlcm_sec'].format(mention=await user_link_html(from_id))
        await message.reply(text, buttons=buttons)


async def do_cleanwelcome(message, chat_id, welc_msg):
    clean_welcome = mongodb.clean_welcome.find_one({'chat_id': chat_id})
    if clean_welcome:
        new = {
            'chat_id': chat_id,
            'enabled': True,
            'last_msg': welc_msg.id
        }
        if 'last_msg' in clean_welcome:
            owo = []
            owo.append(clean_welcome['last_msg'])
            try:
                await tbot.delete_messages(chat_id, owo)
            except MessageDeleteForbiddenError:
                pass

        mongodb.clean_welcome.update_one({'_id': clean_welcome['_id']}, {'$set': new})


@dp.message_handler(content_types=types.ContentTypes.NEW_CHAT_MEMBERS)
@get_strings_dec("greetings")
async def welcome_trigger(message, strings, **kwargs):
    chat_id = message.chat.id
    from_id = message.from_user.id

    # Don't welcome blacklisted users
    blacklisted = mongodb.blacklisted_users.find_one({'user': from_id})
    if blacklisted:
        return

    # Don't welcome fbanned users
    chat_fed = mongodb.fed_groups.find_one({'chat_id': chat_id})
    if chat_fed:
        fed_id = chat_fed['fed_id']
        is_banned = mongodb.fbanned_users.find_one({'user': from_id, 'fed_id': fed_id})
        if is_banned:
            return

    # Do not welcome yourselve
    bot_id = await tbot.get_me()
    if bot_id.id == from_id:
        return

    reply = message.message_id

    # Cleanservice
    cleaner = mongodb.clean_service.find_one({'chat_id': chat_id})
    if cleaner and cleaner['service']:
        await message.delete()
        reply = None

    welcome = mongodb.welcomes.find_one({'chat_id': chat_id})
    if not welcome:
        welc_msg = await message.reply(strings['welcome_hay'].format(
            mention=await user_link_html(from_id)
        ))
    elif welcome['enabled'] is False:
        welc_msg = None
    else:
        welc_msg = await send_note(
            chat_id, chat_id, reply, welcome['note'],
            show_none=True, from_id=from_id
        )

    # Welcomesecurity
    await do_welcomesecurity(message, strings, from_id, chat_id)

    # Cleanwelcome
    if welc_msg:
        await do_cleanwelcome(message, chat_id, welc_msg)


@decorator.command("setwelcome")
@user_admin_dec
@connection(only_in_groups=True, admin=True)
@get_strings_dec("greetings")
async def setwelcome(message, strings, status, chat_id, chat_title, *args, **kwargs):
    chat = mongodb.chat_list.find_one({'chat_id': int(chat_id)})
    arg = message['text'].split(" ", 2)
    if len(arg) <= 1:
        return
    if status is False:
        await message.reply(chat_id)

    note_name = arg[1]
    off = ['off', 'none', 'disable']
    if note_name in off:
        check = mongodb.welcomes.delete_one({'chat_id': chat})
        if check:
            text = "Welcome disabled for this chat"
        else:
            text = "Welcome didn't setuped yet"
        await message.reply(text)
        return
    note = mongodb.notes.find_one({
        'chat_id': chat_id,
        'name': note_name
    })
    if not note:
        await message.reply(strings["cant_find_note"])
        return
    old = mongodb.welcomes.find_one({'chat_id': chat_id})
    if old:
        mongodb.welcomes.delete_one({'_id': old['_id']})
    mongodb.welcomes.insert_one({
        'chat_id': chat_id,
        'enabled': True,
        'note': note_name
    })
    await message.reply(strings["welcome_set_to_note"].format(note_name),
                        parse_mode=types.ParseMode.HTML)


@decorator.command('cleanservice')
@user_admin_dec
@connection(admin=True, only_in_groups=True)
@get_strings_dec("greetings")
async def cleanservice(message, strings, status, chat_id, chat_title, **kwargs):
    bool = message.get_args().lower()
    enable = ['yes', 'on', 'enable']
    disable = ['no', 'disable']
    old = mongodb.clean_service.find_one({'chat_id': chat_id})
    if bool:
        if bool in enable:
            new = {'chat_id': chat_id, 'service': True}
            if old:
                mongodb.clean_service.update_one({'_id': old['_id']}, {"$set": new}, upsert=False)
            else:
                mongodb.clean_service.insert_one(new)
            await message.reply(strings["serv_yes"].format(chat_name=chat_title))
        elif bool in disable:
            mongodb.clean_service.delete_one({'_id': old['_id']})
            await message.reply(strings["serv_no"].format(chat_name=chat_title))
        else:
            await message.reply(strings["no_args_serv"])
            return
    else:
        await message.reply(strings["no_args_serv"])
        return


@decorator.command('welcomesecurity')
@user_admin_dec
@connection(admin=True, only_in_groups=True)
@get_strings_dec("greetings")
async def welcomeSecurity(message, strings, status, chat_id, chat_title, **kwargs):
    args = message.get_args().lower()
    hard = ['hard', 'high']
    soft = ['soft', 'low']
    off = ['off', 'no']
    old = mongodb.welcome_security.find_one({'chat_id': chat_id})
    if not args:
        await message.reply(strings['noArgs'])
        return
    if args in hard:
        if old:
            mongodb.welcome_security.update_one({'_id': old['_id']}, {'$set': {'security': 'hard'}})
        else:
            mongodb.welcome_security.insert_one({'chat_id': chat_id, 'security': 'hard'})
        await message.reply(strings['wlcm_sec_hard'].format(chat_name=chat_title))
    elif args in soft:
        if old:
            mongodb.welcome_security.update_one({'_id': old['_id']}, {'$set': {'security': 'soft'}})
        else:
            mongodb.welcome_security.insert_one({'chat_id': chat_id, 'security': 'soft'})
        await message.reply(strings['wlcm_sec_soft'].format(chat_name=chat_title))
    elif args in off:
        mongodb.welcome_security.delete_one({'chat_id': chat_id})
        await message.reply(strings['wlcm_sec_off'].format(chat_name=chat_title))


@decorator.command('cleanwelcome')
@user_admin_dec
@connection(admin=True, only_in_groups=True)
@get_strings_dec("greetings")
async def clean_welcome(message, strings, status, chat_id, chat_title, **kwargs):
    args = message.get_args().lower()
    on = ['on', 'yes', 'enable']
    off = ['off', 'no', 'disable']
    old = mongodb.clean_welcome.find_one({'chat_id': chat_id})
    if not args:
        if old:
            await message.reply(strings["cln_wel_enabled"].format(chat_name=chat_title))
        else:
            await message.reply(strings["cln_wel_disabled"].format(chat_name=chat_title))
    if args in on:
        if old:
            await message.reply(strings["cln_wel_alr_enabled"].format(chat_name=chat_title))
            return
        else:
            mongodb.clean_welcome.insert_one({"chat_id": chat_id, "enabled": True})
        await message.reply(strings['cln_wel_s_enabled'].format(chat_name=chat_title))
    elif args in off:
        check = mongodb.clean_welcome.delete_one({'chat_id': chat_id})
        if check.deleted_count < 1:
            await message.reply(strings['cln_wel_alr_disabled'].format(chat_name=chat_title))
            return
        await message.reply(strings['cln_wel_s_disabled'].format(chat_name=chat_title))


@decorator.CallBackQuery('wlcm_')
@get_strings_dec("greetings")
async def welcm_btn_callback(event, strings):
    data = str(event.data)
    details = re.search(r'wlcm_(.*)_(.*)', data)
    target_user = details.group(1)
    target_group = details.group(2)[:-1]
    user = event.query.user_id
    chat = event.chat_id
    if int(target_group) == int(chat) is False:
        return
    if int(user) != int(target_user):
        await event.answer(strings['not_trgt'])
        return
    await unmute_user(event, user, chat)
    await event.answer(strings['trgt_success'])
    await event.delete()
