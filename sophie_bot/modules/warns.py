import random
import re
import string

from aiogram.types.inline_keyboard import (InlineKeyboardButton,
                                           InlineKeyboardMarkup)

from sophie_bot import BOT_ID
from sophie_bot.decorator import register
from sophie_bot.services.mongo import db

from .utils.connections import chat_connection
from .utils.language import get_strings_dec
from .utils.restrictions import ban_user
from .utils.user_details import get_user_dec, get_user_link, is_user_admin


@register(cmds='warn', user_can_restrict_members=True, bot_can_restrict_members=True)
@chat_connection(admin=True, only_groups=True)
@get_user_dec()
@get_strings_dec('warns')
async def warn(message, chat, user, strings):
    chat_id = chat['chat_id']
    chat_title = chat['chat_title']
    by = message.from_user.id
    user_id = user['user_id']
    warn_id = randomString(15)

    if user_id == BOT_ID:
        await message.reply(strings['warn_sofi'])
        return

    elif user_id == message.from_user.id:
        await message.reply(strings['warn_self'])
        return

    elif await is_user_admin(chat_id, user_id):
        await message.reply(strings['warn_admin'])
        return

    args = message.get_args().split(' ', 1)
    print(args)
    if len(args) >= 1:
        reason = ' '.join(args[0:])
    else:
        reason = None

    await db.warns_v2.insert_one({
        'warn_id': warn_id,
        'user_id': user_id,
        'chat_id': chat_id,
        'reason': str(reason),
        'by': by
    })

    admin = await get_user_link(message.from_user.id)
    member = await get_user_link(user_id)
    text = strings['warn'].format(admin=admin, user=member, chat_name=chat_title)

    if reason:
        text += strings['warn_rsn'].format(reason=reason)

    wrns = db.warns_v2.find({'chat_id': chat_id, 'user_id': user_id})
    warn_count = 0
    async for wrn in wrns:
        warn_count += 1

    button = InlineKeyboardMarkup().add(InlineKeyboardButton(
        "⚠️ Remove warn", callback_data='remove_warn_{}'.format(warn_id)
    ))

    # TODO(Rules button)

    if (warn_limit := await db.warnlimit.find_one({'chat_id':chat_id})):
        max_warn = int(warn_limit['num'])
    else:
        max_warn = 3

    if warn_count >= max_warn:
        await ban_user(str(chat_id), str(user_id))
        return

        text = strings['warn_bun'].format(user=user)
        await db.warns_v2.delete_many({'user_id': user_id, 'chat_id': chat_id})
    else:
        text += strings['warn_num'].format(curr_warns=warn_count, max_warns=max_warn)

    await message.reply(text, reply_markup=button, disable_web_page_preview=True)


@register(regexp=r'remove_warn_(.*)', f='cb', allow_kwargs=True)
@get_strings_dec('warns')
async def rmv_warn_btn(event, strings, regexp=None, **kwargs):
    warn_id = re.search(r'remove_warn_(.*)', str(regexp)).group(1)[:-2]
    chat_id = event.message.chat.id
    user_id = event.message.from_user.id
    admin = await get_user_link(user_id)

    if not await is_user_admin(chat_id, user_id):
        await event.answer(strings['warn_no_admin_alert'], show_alert=True)
        return

    await db.warns_v2.delete_one({'chat_id': chat_id, 'warn_id': warn_id})

    await event.message.edit_text(strings['warn_btn_rmvl_sucess'].format(admin=admin))


@register(cmds='warns')
@chat_connection(admin=True, only_groups=True)
@get_user_dec()
@get_strings_dec('warns')
async def warns(message, chat, user, strings):
    chat_id = chat['chat_id']
    user_id = user['user_id']
    text = strings['warns_header']
    user = await get_user_link(user_id)

    warns = db.warns_v2.find({'user_id':user_id, 'chat_id': chat_id})

    count = 0
    async for warn in warns:
        count += 1
        print(warn)
        by = await get_user_link(warn['by'])
        reason = warn['reason']
        if not reason or reason == 'None':
            reason = '__No Reason__'
        text += strings['warns'].format(count=count, reason=reason, admin=by)

    if count == 0:
        await message.reply(strings['no_warns'].format(user=user))
        return

    await message.reply(text)


@register(cmds='warnlimit', user_admin=True)
@chat_connection(admin=True, only_groups=True)
@get_strings_dec('warns')
async def warnlimit(message, chat, strings):
    chat_id = chat['chat_id']
    chat_title = chat['chat_title']
    arg = message.get_args().split(' ', 1)[0]

    if not arg:
        if (current_limit := db.warnlimit.find_one({'chat_id': chat_id})):
            num = current_limit['num']
        else:
            num = 3  # Default value
        await message.reply(strings['warn_limit'].format(chat_name=chat_title, num=num))
    else:
        if int(arg) < 2:
            return await message.reply(strings['warnlimit_short'])

        new = {
            'chat_id': chat_id,
            'num': int(arg)
        }

        await db.warnlimit.update_one({'chat_id': chat_id}, {'$set': new}, upsert=True)
        await message.reply(strings['warnlimit_updated'].format(num=arg))


@register(cmds='resetwarns', user_can_restrict_members=True)
# @register (cmds='resetwarns', user_admin=True)
@chat_connection(admin=True, only_groups=True)
@get_user_dec()
@get_strings_dec('warns')
async def resetwarn(message, chat, user, strings):
    chat_id = chat['chat_id']
    chat_title = chat['chat_title']
    user_id = user['user_id']
    user = await get_user_link(user_id)
    admin = await get_user_link(message.from_user.id)

    if user_id == BOT_ID:
        await message.reply(strings['rst_wrn_sofi'])
        return

    if (chk := await db.warns_v2.find_one({'chat_id': chat_id, 'user_id': user_id})):
        print(chk)
        deleted = await db.warns_v2.delete_many({'chat_id': chat_id, 'user_id': user_id})
        purged = deleted.deleted_count
        await message.reply(strings['purged_warns'].format(
            admin=admin, num=purged, user=user, chat_title=chat_title))
    else:
        await message.reply(strings['usr_no_wrn'].format(user=user))


def randomString(stringLength):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for i in range(stringLength))
