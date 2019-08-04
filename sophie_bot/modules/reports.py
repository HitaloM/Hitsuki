from sophie_bot import WHITELISTED, decorator, mongodb, dp
from sophie_bot.modules.connections import connection
from sophie_bot.modules.language import get_strings_dec
from sophie_bot.modules.users import is_user_admin, user_link_html, get_chat_admins, aio_get_user
from aiogram.types import Message


@dp.message_handler(regexp="^@admin")
@connection(only_in_groups=True)
@get_strings_dec('reports')
async def admin_handler(message: Message, strings, *args, **kwargs):
    from_id = message.from_user.id

    if (await is_user_admin(message.chat.id, from_id)) is True:
        return await message.reply(strings['user_is_admin'])

    if from_id in WHITELISTED:
        return await message.reply(strings['user_is_whitelisted'])

    in_db = mongodb.reports.find_one({'chat_id': message.chat.id})
    if not in_db:
        mongodb.reports.insert_one({
            'chat_id': message.chat.id,
            'status': False
        })
        return await message.reply(strings['reports_disabled'])
    elif in_db['status'] is False:
        return await message.reply(strings['reports_disabled'])
    else:
        if "reply_to_message" not in message:
            return await message.reply(strings['no_user_to_report'])

        reply_id = message.reply_to_message.from_user.id

        if (await is_user_admin(message.chat.id, reply_id)) is True:
            return await message.reply(strings['report_admin'])

        if reply_id in WHITELISTED:
            return await message.reply(strings['report_whitedlisted'])

        admins = await get_chat_admins(message.chat.id)
        reported = await user_link_html(message.reply_to_message.from_user.id)
        text = strings['reported_user'].format(user=reported)

        try:
            if message.text.split(None, 2)[1]:
                text += strings['reported_reason'].format(reason=message.text.split(None, 2)[1])
        except Exception:
            pass

        for admin in admins:
            text += await user_link_html(admin, custom_name="‏")

        await message.reply(text)


@decorator.command("report")
@connection(only_in_groups=True)
@get_strings_dec('reports')
async def report_user(message, strings, status, chat_id, chat_title):
    from_id = message.from_user.id
    if (await is_user_admin(message.chat.id, from_id)) is True:
        return await message.reply(strings['user_is_admin'])

    if from_id in WHITELISTED:
        return await message.reply(strings['user_is_whitelisted'])

    user, text = await aio_get_user(message)

    in_db = mongodb.reports.find_one({'chat_id': message.chat.id})
    if not in_db:
        mongodb.reports.insert_one({
            'chat_id': message.chat.id,
            'status': False
        })
        return await message.reply(strings['reports_disabled'])
    elif in_db['status'] is False:
        return await message.reply(strings['reports_disabled'])
    else:
        if not user:
            return await message.reply(strings['no_user_to_report'])

        reply_id = user['user_id']

        if (await is_user_admin(message.chat.id, reply_id)) is True:
            return await message.reply(strings['report_admin'])

        if reply_id in WHITELISTED:
            return await message.reply(strings['report_whitedlisted'])

        admins = await get_chat_admins(message.chat.id)
        reported = await user_link_html(user['user_id'])
        msg = strings['reported_user'].format(user=reported)

        if text:
            msg += strings['reported_reason'].format(reason=text)

        for admin in admins:
            msg += await user_link_html(admin, custom_name="‏")

        await message.reply(msg)


@decorator.command("reports")
@connection(only_in_groups=True)
@get_strings_dec('reports')
async def reports(message, strings, status, chat_id, chat_title):
    text = message.text.split(None, 2)

    reports = mongodb.reports.find_one({
        'chat_id': chat_id
    })

    if not reports:
        mongodb.reports.insert_one({
            'chat_id': chat_id,
            'status': False
        })

        reports = dict({'status': False})

    if not text[1:]:
        if reports['status'] is False:
            return await message.reply(strings['reports_on'])
        else:
            return await message.reply(strings['reports_on'])
    else:
        if (await is_user_admin(chat_id, message.from_user.id)) is False:
            return await message.reply(strings['user_not_admin'])
        else:
            if text[1].lower().find('yes') is 0 or text[1].lower().find('on') is 0:
                    if reports['status'] is True:
                        return await message.reply(strings['reports_already_on'])
                    else:
                        mongodb.reports.update_one({'chat_id': chat_id}, {
                            "$set": {
                                'status': True
                            }
                        })

                        return await message.reply(strings['reports_turned_on'])
            if text[1].lower().find('no') is 0 or text[1].lower().find('off') is 0:
                    if reports['status'] is False:
                        return await message.reply(strings['reports_already_off'])
                    else:
                        mongodb.reports.update_one({'chat_id': chat_id}, {
                            "$set": {
                                'status': False
                            }
                        })

                        return await message.reply(strings['reports_off'])
            else:
                return await message.reply(strings['wrong_argument'])
