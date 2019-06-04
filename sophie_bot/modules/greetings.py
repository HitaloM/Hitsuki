import re
import time

from telethon.tl.custom import Button

from sophie_bot import bot, decorator, mongodb
from sophie_bot.modules.bans import mute_user, unmute_user
from sophie_bot.modules.connections import get_conn_chat
from sophie_bot.modules.helper_func.flood import flood_limit
from sophie_bot.modules.connections import connection
from sophie_bot.modules.language import get_string, get_strings_dec
from sophie_bot.modules.notes import send_note
from sophie_bot.modules.users import user_admin_dec, user_link


@decorator.ChatAction()
@get_strings_dec("greetings")
async def welcome_trigger(event, strings):
    if event.user_joined is True or event.user_added is True:
        chat = event.chat_id
        chat = mongodb.chat_list.find_one({'chat_id': int(chat)})

        user_id = event.action_message.from_id
        bot_id = await bot.get_me()
        if bot_id.id == user_id:
            return  # Do not welcome yourselve

        chat_id = event.action_message.chat_id
        cleaner = mongodb.clean_service.find_one({'chat_id': chat_id})
        if cleaner and cleaner['service']:
            await event.delete()

        if hasattr(event.action_message.action, 'users'):
            from_id = event.action_message.action.users[0]
        else:
            from_id = event.action_message.from_id

        welcome = mongodb.welcomes.find_one({'chat_id': chat_id})
        if not welcome:
            await event.reply(strings['welcome_hay'].format(mention=await user_link(from_id)))
        elif welcome['enabled'] is False:
            pass
        else:
            welc_msg = await send_note(event.chat_id, chat_id, event.action_message.id,
                                       welcome['note'], show_none=True, from_id=from_id)
        welcome_security = mongodb.welcome_security.find_one({'chat_id': chat_id})
        if welcome_security and welcome_security['security'] == 'soft':
            buttons = [
                [Button.inline(strings['clik2tlk_btn'], 'wlcm_{}_{}'.format(from_id, chat_id))]
            ]
            time_val = int(time.time() + 60 * 60)  # Mute 1 hour
            try:
                await mute_user(event, user_id, chat_id, time_val)
            except Exception as err:
                await event.reply(err)

            text = strings['wlcm_sec'].format(mention=await user_link(from_id))
            await event.reply(text, buttons=buttons)

        elif welcome_security and welcome_security['security'] == 'hard':
            buttons = [
                [Button.inline(strings['clik2tlk_btn'], 'wlcm_{}_{}'.format(from_id, chat_id))]
            ]
            try:
                await mute_user(event, user_id, chat_id, None)
            except Exception as err:
                await event.reply(err)

            text = strings['wlcm_sec'].format(mention=await user_link(from_id))
            await event.reply(text, buttons=buttons)

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
                await event.client.delete_messages(chat_id, owo)

            mongodb.clean_welcome.update_one({'_id': clean_welcome['_id']}, {'$set': new})


@decorator.command("setwelcome", arg=True)
async def setwelcome(event):
    if not event.pattern_match.group(1):
        return
    status, chat_id, chat_title = await get_conn_chat(event.from_id, event.chat_id, admin=True)
    chat = event.chat_id
    chat = mongodb.chat_list.find_one({'chat_id': int(chat)})
    if status is False:
        await event.reply(chat_id)
        return
    note_name = event.pattern_match.group(1)
    note = mongodb.notes.find_one({
        'chat_id': chat_id,
        'name': note_name
    })
    if not note:
        await event.reply(get_string("greetings", "cant_find_note", chat))
        return
    old = mongodb.welcomes.find_one({'chat_id': chat_id})
    if old:
        mongodb.welcomes.delete_one({'_id': old['_id']})
    mongodb.welcomes.insert_one({
        'chat_id': chat_id,
        'enabled': True,
        'note': note_name
    })
    await event.reply(get_string("greetings", "welcome_set_to_note", chat).format(note_name))


@decorator.command("setwelcome")
async def setwelcome_withot_args(event):
    chat = event.chat_id
    chat = mongodb.chat_list.find_one({'chat_id': int(chat)})
    if await flood_limit(event, 'setwelcome') is False:
        return
    status, chat_id, chat_title = await get_conn_chat(
        event.from_id, event.chat_id, only_in_groups=True)
    if status is False:
        await event.reply(chat_id)
        return
    old = mongodb.welcomes.find_one({'chat_id': chat_id})
    if old:
        note_name = old['note']
        await event.reply(get_string("greetings", "welcome_is_note", chat).format(note_name))
    else:
        await event.reply(get_string("greetings", "welcome_is_default", chat))


@decorator.command('cleanservice', arg=True)
@user_admin_dec
async def cleanservice(event):
    args = event.pattern_match.group(1)
    chat_id = event.chat_id
    enable = ['yes', 'on', 'enable']
    disable = ['no', 'disable']
    bool = args.lower()
    old = mongodb.clean_service.find_one({'chat_id': chat_id})
    if bool:
        if bool in enable:
            new = {'chat_id': chat_id, 'service': True}
            if old:
                mongodb.clean_service.update_one({'_id': old['_id']}, {"$set": new}, upsert=False)
            else:
                mongodb.clean_service.insert_one(new)
            await event.reply(get_string("greetings", "serv_yes", chat_id))
        elif bool in disable:
            mongodb.clean_service.delete_one({'_id': old['_id']})
            await event.reply(get_string("greetings", "serv_no", chat_id))
        else:
            await event.reply(get_string("greetings", "no_args_serv", chat_id))
            return
    else:
        await event.reply(get_string("greetings", "no_args_serv", chat_id))
        return


@decorator.command('welcomesecurity', arg=True)
@user_admin_dec
@get_strings_dec("greetings")
async def welcomeSecurity(event, strings):
    arg = event.pattern_match.group(1)
    args = arg.lower()
    hard = ['hard', 'high']
    soft = ['soft', 'low']
    off = ['off', 'no']
    chat = event.chat_id
    old = mongodb.welcome_security.find_one({'chat_id': chat})
    if not args:
        await event.reply(strings['noArgs'])
        return
    if args in hard:
        if old:
            mongodb.welcome_security.update_one({'_id': old['_id']}, {'$set': {'security': 'hard'}})
        else:
            mongodb.welcome_security.insert_one({'chat_id': chat, 'security': 'hard'})
        await event.reply(strings['wlcm_sec_hard'])
    elif args in soft:
        if old:
            mongodb.welcome_security.update_one({'$set': {'security': 'soft'}})
        else:
            mongodb.welcome_security.insert_one({'chat_id': chat, 'security': 'soft'})
        await event.reply(strings['wlcm_sec_soft'])
    elif args in off:
        mongodb.welcome_security.delete_one({'chat_id': chat})
        await event.reply(strings['wlcm_sec_off'])


@decorator.command('cleanwelcome', arg=True)
@user_admin_dec
@connection(admin=True, only_in_groups=True)
@get_strings_dec("greetings")
async def clean_welcome(event, strings, status, chat_id, chat_title):
    arg = event.pattern_match.group(1)
    args = arg.lower()
    on = ['on', 'yes', 'enable']
    off = ['off', 'no', 'disable']
    old = mongodb.clean_welcome.find_one({'chat_id': chat_id})
    if not args:
        if old:
            await event.reply(strings["cln_wel_enabled"].format(chat_name=chat_title))
        else:
            await event.reply(strings["cln_wel_disabled"].format(chat_name=chat_title))
    if args in on:
        if old:
            await event.reply(strings["cln_wel_alr_enabled"].format(chat_name=chat_title))
            return
        else:
            mongodb.clean_welcome.insert_one({"chat_id": chat_id, "enabled": True})
        await event.reply(strings['cln_wel_s_enabled'].format(chat_name=chat_title))
    elif args in off:
        check = mongodb.clean_welcome.delete_one({'chat_id': chat_id})
        if check.deleted_count < 1:
            await event.reply(strings['cln_wel_alr_disabled'].format(chat_name=chat_title))
            return
        await event.reply(strings['cln_wel_s_disabled'].format(chat_name=chat_title))


@decorator.CallBackQuery('wlcm_')
@get_strings_dec("greetings")
async def welcm_btn_callback(event, strings):
    data = str(event.data)
    details = re.search(r'wlcm_(.*)_(.*)', data)
    target_user = details.group(1)
    target_group = details.group(2)[:-1]
    user = event.query.user_id
    chat = event.chat_id
    if target_group == chat is False:
        return
    if user != target_user:
        await event.answer(strings['not_trgt'])
        return
    await unmute_user(event, user, chat)
    await event.answer(strings['trgt_success'])
    await event.delete()
