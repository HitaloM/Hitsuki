from time import gmtime, strftime

from sophie_bot import SUDO, decorator, mongodb, logger
from sophie_bot.modules.users import user_admin_dec, get_user_and_text, get_user, user_link
from sophie_bot.modules.connections import connection
from sophie_bot.modules.bans import ban_user, unban_user


@decorator.command("antispam", arg=True)
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


@decorator.command("gban", arg=True, from_users=SUDO)
async def blacklist_user(event):
    chat_id = event.chat_id
    user, reason = await get_user_and_text(event)
    if not reason:
        await event.reply("You can't blacklist user without a reason blyat!")
        return
    try:
        a
    except Exception as err:
        await event.reply(err)
        logger.error(err)
    old = mongodb.blacklisted_users.find_one({'user': user['user_id']})
    if old:
        new = {
            'user': user['user_id'],
            'date': old['date'],
            'by': old['by'],
            'reason': reason
        }
        mongodb.notes.update_one({'_id': old['_id']}, {"$set": new}, upsert=False)
        await event.reply("This user already blacklisted! I'll update the reason.")
        return
    date = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    new = {
        'user': user['user_id'],
        'date': date,
        'reason': reason,
        'by': event.from_id
    }
    user_id = user['user_id']
    logger.info(f'user {user_id} gbanned by {event.from_id}')
    mongodb.blacklisted_users.insert_one(new)
    await event.reply("Sudo {} blacklisted {}.\nDate: `{}`\nReason: `{}`".format(
        await user_link(event.from_id), await user_link(user['user_id']), date, reason))


@decorator.command("ungban", arg=True, from_users=SUDO)
async def un_blacklist_user(event):
    chat_id = event.chat_id
    user = await get_user(event)
    try:
        await unban_user(event, user['user_id'], chat_id)
    except Exception as err:
        await event.reply(err)
        logger.error(err)
    old = mongodb.blacklisted_users.find_one({'user': user['user_id']})
    if not old:
        await event.reply("This user isn't blacklisted!")
        return
    user_id = user['user_id']
    logger.info(f'user {user_id} ungbanned by {event.from_id}')
    mongodb.blacklisted_users.delete_one({'_id': old['_id']})
    await event.reply("Sudo {} unblacklisted {}.".format(
        await user_link(event.from_id), await user_link(user_id)))


@decorator.insurgent()
async def welcome_trigger(event):
    user_id = event.action_message.from_id
    K = mongodb.blacklisted_users.find_one({'user': user_id})
    if K:
        try:
            await ban_user(event, K['user_id'], event.chat_id, None)
        except Exception as err:
            await event.reply(err)
            logger.error(err)
        await event.reply("User {} blacklisted.\nReason: {}".format(
            user_link(user_id), K['reason']))
