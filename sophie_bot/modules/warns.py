import re

from aiogram.types.inline_keyboard import (
	InlineKeyboardButton,
	InlineKeyboardMarkup
)
from bson.objectid import ObjectId

from sophie_bot import BOT_ID
from sophie_bot.decorator import register
from sophie_bot.services.mongo import db
from .utils.connections import chat_connection
from .utils.language import get_strings_dec
from .utils.restrictions import ban_user
from .utils.user_details import (
	get_user_and_text_dec, get_user_dec,
	get_user_link, is_user_admin
)


@register(cmds='warn', user_can_restrict_members=True, bot_can_restrict_members=True)
@chat_connection(admin=True, only_groups=True)
@get_user_and_text_dec()
@get_strings_dec('warns')
async def warn(message, chat, user, text, strings):
    chat_id = chat['chat_id']
    chat_title = chat['chat_title']
    by_id = message.from_user.id
    user_id = user['user_id']

    if user_id == BOT_ID:
        await message.reply(strings['warn_sofi'])
        return

    elif user_id == message.from_user.id:
        await message.reply(strings['warn_self'])
        return

    elif await is_user_admin(chat_id, user_id):
        await message.reply(strings['warn_admin'])
        return

    reason = text
    warn_id = str((await db.warns_v2.insert_one({
        'user_id': user_id,
        'chat_id': chat_id,
        'reason': str(reason),
        'by': by_id
    })).inserted_id)

    admin = await get_user_link(message.from_user.id)
    member = await get_user_link(user_id)
    text = strings['warn'].format(admin=admin, user=member, chat_name=chat_title)

    if reason:
        text += strings['warn_rsn'].format(reason=reason)

    warns_count = await db.warns_v2.count_documents({'chat_id': chat_id, 'user_id': user_id})

    button = InlineKeyboardMarkup().add(InlineKeyboardButton(
        "⚠️ Remove warn", callback_data='remove_warn_{}'.format(warn_id)
    ))

    # TODO(Rules button)

    if warn_limit := await db.warnlimit.find_one({'chat_id': chat_id}):
        max_warn = int(warn_limit['num'])
    else:
        max_warn = 3

    if warns_count >= max_warn:
        await ban_user(str(chat_id), str(user_id))
        await message.reply(strings['warn_bun'].format(user=member))
        db.warns_v2.delete_many({'user_id': user_id, 'chat_id': chat_id})
        return
    else:
        text += strings['warn_num'].format(curr_warns=warns_count, max_warns=max_warn)

    await message.reply(text, reply_markup=button, disable_web_page_preview=True)


@register(regexp=r'remove_warn_(.*)', f='cb', allow_kwargs=True)
@get_strings_dec('warns')
async def rmv_warn_btn(event, strings, regexp=None, **kwargs):
    warn_id = ObjectId(re.search(r'remove_warn_(.*)', str(regexp)).group(1)[:-2])
    chat_id = event.message.chat.id
    user_id = event.from_user.id
    admin_link = await get_user_link(user_id)

    if not await is_user_admin(chat_id, user_id):
        await event.answer(strings['warn_no_admin_alert'], show_alert=True)
        return

    await db.warns_v2.delete_one({'_id': warn_id})

    await event.message.edit_text(strings['warn_btn_rmvl_success'].format(admin=admin_link))


@register(cmds='warns')
@chat_connection(admin=True, only_groups=True)
@get_user_dec(allow_self=True)
@get_strings_dec('warns')
async def warns(message, chat, user, strings):
    chat_id = chat['chat_id']
    user_id = user['user_id']
    text = strings['warns_header']
    user_link = await get_user_link(user_id)

    count = 0
    async for warn in db.warns_v2.find({'user_id': user_id, 'chat_id': chat_id}):
        count += 1
        by = await get_user_link(warn['by'])
        rsn = warn['reason']
        reason = f"<code>{rsn}</code>"
        if not rsn or rsn == 'None':
            reason = '<i>No Reason</i>'
        text += strings['warns'].format(count=count, reason=reason, admin=by)

    if count == 0:
        await message.reply(strings['no_warns'].format(user=user_link))
        return

    await message.reply(text)


@register(cmds='warnlimit', user_admin=True)
@chat_connection(admin=True, only_groups=True)
@get_strings_dec('warns')
async def warnlimit(message, chat, strings):
    chat_id = chat['chat_id']
    chat_title = chat['chat_title']
    arg = int(message.get_args().split(' ', 1)[0])

    if not arg:
        if current_limit := db.warnlimit.find_one({'chat_id': chat_id}):
            num = current_limit['num']
        else:
            num = 3  # Default value
        await message.reply(strings['warn_limit'].format(chat_name=chat_title, num=num))
    else:
        if arg < 2:
            return await message.reply(strings['warnlimit_short'])

        elif arg > 10000:  # Max value
            return await message.reply(strings['warnlimit_long'])

        new = {
            'chat_id': chat_id,
            'num': arg
        }

        await db.warnlimit.update_one({'chat_id': chat_id}, {'$set': new}, upsert=True)
        await message.reply(strings['warnlimit_updated'].format(num=arg))


@register(cmds=['resetwarns', 'delwarns'], user_can_restrict_members=True)
@chat_connection(admin=True, only_groups=True)
@get_user_dec()
@get_strings_dec('warns')
async def reset_warn(message, chat, user, strings):
    chat_id = chat['chat_id']
    chat_title = chat['chat_title']
    user_id = user['user_id']
    user_link = await get_user_link(user_id)
    admin_link = await get_user_link(message.from_user.id)

    if user_id == BOT_ID:
        await message.reply(strings['rst_wrn_sofi'])
        return

    if await db.warns_v2.find_one({'chat_id': chat_id, 'user_id': user_id}):
        deleted = await db.warns_v2.delete_many({'chat_id': chat_id, 'user_id': user_id})
        purged = deleted.deleted_count
        await message.reply(strings['purged_warns'].format(
            admin=admin_link, num=purged, user=user_link, chat_title=chat_title))
    else:
        await message.reply(strings['usr_no_wrn'].format(user=user))


async def __export__(chat_id):
    if data := await db.warnlimit.find_one({'chat_id': chat_id}):
        number = data['num']
    else:
        number = 3

    return {'warns': {'warns_limit': number}}


async def __import__(chat_id, data):
    if 'warns_limit' in data:
        number = data['warns_limit']
        if number < 2:
            return

        elif number > 10000:  # Max value
            return

        await db.warnlimit.update_one({'chat_id': chat_id}, {'$set': {'num': number}}, upsert=True)
