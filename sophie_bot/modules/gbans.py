from time import gmtime, strftime
import asyncio

from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights

from sophie_bot import SUDO, WHITELISTED, decorator, logger, mongodb, tbot
from sophie_bot.modules.connections import connection
from sophie_bot.modules.language import get_string, get_strings_dec
from sophie_bot.modules.users import (get_user, get_user_and_text,
                                      user_admin_dec, user_link)
from telethon.tl.functions.channels import GetParticipantRequest


GBANNED_RIGHTS = ChatBannedRights(
    until_date=None,
    view_messages=True,
    send_messages=True,
    send_media=True,
    send_stickers=True,
    send_gifs=True,
    send_games=True,
    send_inline=True,
    embed_links=True,
)


@decorator.t_command("antispam", arg=True)
@user_admin_dec
@connection(admin=True, only_in_groups=True)
async def switch_antispam(event, status, chat_id, chat_title):
    args = event.pattern_match.group(1)
    enable = ['yes', 'on', 'enable']
    disable = ['no', 'disable']
    bool = args.lower()
    old = mongodb.antispam_setting.find_one({'chat_id': chat_id})
    if bool:
        if bool in disable:
            new = {'chat_id': chat_id, 'disabled': True}
            if old:
                mongodb.antispam_setting.update_one(
                    {'_id': old['_id']}, {"$set": new}, upsert=False)
            else:
                mongodb.antispam_setting.insert_one(new)
            await event.reply("Antispam disabled for {chat_name}".format(chat_title))
        elif bool in enable:
            mongodb.clean_service.delete_one({'_id': old['_id']})
            await event.reply("Antispam enabled for {chat_name}".format(chat_title))
        else:
            await event.reply("Heck, i don't undestand what you wanna from me.")
            return
    else:
        if old and old['disabled'] is True:
            txt = 'disabled'
        else:
            txt = 'enabled'
        await event.reply("Antispam for **{}** is **{}**".format(chat_title, txt))
        return


async def blacklist_user(event):
    user, reason = await get_user_and_text(event, send_text=False)

    user_id = int(user['user_id'])

    if user_id in WHITELISTED:
        await event.reply("You can't blacklist a Whitelisted user")
        return

    if not reason:
        await event.reply("You can't blacklist user without a reason blyat!")
        return

    date = strftime("%Y-%m-%d %H:%M:%S", gmtime())

    logger.info(f'user {user_id} gbanned by {event.from_id}')
    text = "{} **blacklisted** {}\n".format(
        await user_link(event.from_id), await user_link(user_id))
    text += "ID: `{}`\n".format(user_id)
    text += "Date: `{}`\n".format(date)
    text += "Reason: `{}`\n".format(reason)
    msg = await event.reply(text + "Status: **Gbanning...**")

    old = mongodb.blacklisted_users.find_one({'user': user_id})
    if old:
        new = {
            'user': user_id,
            'date': old['date'],
            'by': old['by'],
            'reason': reason
        }
        mongodb.blacklisted_users.update_one({'_id': old['_id']}, {"$set": new}, upsert=False)
        await event.reply("This user already blacklisted! I'll update the reason.")
        return

    new = {
        'user': user_id,
        'date': date,
        'reason': reason,
        'by': event.from_id
    }

    mongodb.blacklisted_users.insert_one(new)

    gbanned_ok = 0
    gbanned_error = 0
    if 'chats' not in user:
        try:
            await event.client(EditBannedRequest(
                event.chat_id,
                user_id,
                GBANNED_RIGHTS
            ))
        except Exception:
            pass
        await msg.edit(text + "Status: **User not gbanned in any chat, but added in blacklist.**")
        return

    for chat in user['chats']:
        await asyncio.sleep(0.2)
        try:
            user_a = await tbot(GetParticipantRequest(channel=event.chat_id, user_id=user_id))
            if not user_a:
                continue
            await event.client(EditBannedRequest(
                chat['chat_id'],
                user_id,
                GBANNED_RIGHTS
            ))
            await event.reply(msg)
            gbanned_ok += 1
        except Exception:
            gbanned_error += 1
            continue
    await msg.edit(text + "Status: **Done, user gbanned in {}/{} chats.**".format(
        gbanned_ok, gbanned_error
    ))


@decorator.t_command("gban", arg=True, from_users=SUDO)
async def gban_1(event):
    await blacklist_user(event)


@decorator.t_command("fban", arg=True, from_users=172811422)
async def gban_2(event):
    await blacklist_user(event)


@decorator.t_command("ungban", arg=True, from_users=SUDO)
async def un_blacklist_user(event):
    chat_id = event.chat_id
    user = await get_user(event, send_text=False)

    probably_id = event.pattern_match.group(1).split(" ")[0]

    if user:
        user_id = int(user['user_id'])
    if not user and probably_id.isdigit():
        user_id = int(probably_id)

    try:
        unbanned_rights = ChatBannedRights(
            until_date=None,
            view_messages=False,
            send_messages=False,
            send_media=False,
            send_stickers=False,
            send_gifs=False,
            send_games=False,
            send_inline=False,
            embed_links=False,
        )

        precheck = mongodb.gbanned_groups.find({'user': user})
        if precheck:
            chats = mongodb.gbanned_groups.find({'user': user})
        else:
            chats = chat_id
        for chat in chats:
            await event.client(
                EditBannedRequest(
                    chat['chat'],
                    user_id,
                    unbanned_rights
                )
            )

    except Exception as err:
        logger.error(str(err))
    old = mongodb.blacklisted_users.find_one({'user': user_id})
    if not old:
        await event.reply("This user isn't blacklisted!")
        return
    logger.info(f'user {user_id} ungbanned by {event.from_id}')
    mongodb.blacklisted_users.delete_one({'_id': old['_id']})
    await event.reply("Sudo {} unblacklisted {}.".format(
        await user_link(event.from_id), await user_link(user_id)))


@decorator.insurgent()
async def gban_trigger(event):
    user_id = event.from_id

    K = mongodb.blacklisted_users.find_one({'user': user_id})
    if K:
        banned_rights = ChatBannedRights(
            until_date=None,
            view_messages=True,
            send_messages=True,
            send_media=True,
            send_stickers=True,
            send_gifs=True,
            send_games=True,
            send_inline=True,
            embed_links=True,
        )

        try:
            ban = await event.client(
                EditBannedRequest(
                    event.chat_id,
                    user_id,
                    banned_rights
                )
            )

            if ban:
                mongodb.gbanned_groups.insert_one({'user': user_id, 'chat': event.chat_id})
                await event.reply(get_string("gbans", "user_is_blacklisted", event.chat_id).format(
                                  await user_link(user_id), K['reason']))

        except Exception:
            pass


@decorator.ChatAction()
@get_strings_dec('gbans')
async def gban_helper_2(event, strings):
    if event.user_joined is True or event.user_added is True:
        await asyncio.sleep(2)  # Sleep 2 seconds before check user to allow Simon gban user
        if hasattr(event.action_message.action, 'users'):
            from_id = event.action_message.action.users[0]
        else:
            from_id = event.action_message.from_id

        K = mongodb.blacklisted_users.find_one({'user': from_id})
        if not K:
            return

        banned_rights = ChatBannedRights(
            until_date=None,
            view_messages=True,
            send_messages=True,
            send_media=True,
            send_stickers=True,
            send_gifs=True,
            send_games=True,
            send_inline=True,
            embed_links=True,
        )

        try:
            ban = await event.client(
                EditBannedRequest(
                    event.chat_id,
                    from_id,
                    banned_rights
                )
            )

            if ban:
                mongodb.gbanned_groups.insert_one({'user': from_id, 'chat': event.chat_id})
                msg = await event.reply(strings['user_is_blacklisted'].format(
                                        user=await user_link(from_id), rsn=K['reason']))
                await asyncio.sleep(5)
                await event.client.delete_messages(event.chat_id, msg)

        except Exception as err:
            logger.info(f'Error on gbanning {from_id} in {event.chat_id} \n {err}')
            pass
