from sophie_bot.decorator import register
from sophie_bot.services.mongo import db

from .utils.connections import chat_connection
from .utils.disable import disablable_dec
from .utils.language import get_strings_dec
from .utils.user_details import get_admins_rights, get_user_link, is_user_admin


@register(regexp='^@admins')
@chat_connection(only_groups=True)
@get_strings_dec('reports')
async def report1_cmd(message, chat, strings):
	# Checking whether report is disabled in chat!
	check = await db.disabled_v2.find_one({'chat_id': chat['chat_id']})
	if check:
		if 'report' in check['cmds']:
			return
	await report(message, chat, strings)


@register(cmds="report")
@chat_connection(only_groups=True)
@disablable_dec('report')
@get_strings_dec('reports')
async def report2_cmd(message, chat, strings):
	await report(message, chat, strings)


async def report(message, chat, strings):
	user = message.from_user.id

	if (await is_user_admin(chat['chat_id'], user)) is True:
		return await message.reply(strings['user_user_admin'])

	if 'reply_to_message' not in message:
		return await message.reply(strings['no_user_to_report'])

	offender_id = message.reply_to_message.from_user.id
	print(offender_id)
	if (await is_user_admin(chat['chat_id'], offender_id)) is True:
		return await message.reply(strings['report_admin'])

	admins = await get_admins_rights(chat['chat_id'])

	offender = await get_user_link(offender_id)
	text = strings['reported_user'].format(user=offender)

	try:
		if message.text.split(None, 2)[1]:
			reason = ' '.join(message.text.split(None, 2)[1:])
			text += strings['reported_reason'].format(reason=reason)
	except Exception:
		pass

	for admin in admins:
		text += await get_user_link(admin, custom_name="‎ ")

	await message.reply(text)
