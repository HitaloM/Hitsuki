from aiogram.types.inline_keyboard import InlineKeyboardMarkup, InlineKeyboardButton

from sophie_bot import CONFIG, dp, bot
from sophie_bot.modules.users import is_user_admin


@dp.callback_query_handler(regexp='report_error')
async def report_error(query):
    channel_id = CONFIG['advanced']['errors_channel']
    chat_id = query.message.chat.id
    if await is_user_admin(chat_id, query.from_user.id) is False:
        await query.answer("Only admins can report errors!")
        return
    await bot.forward_message(channel_id, chat_id, query.message.message_id)

    buttons = InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton("Delete message",
                             callback_data='get_delete_msg_{}_admin'.format(chat_id))
    )

    await bot.edit_message_caption(
        chat_id,
        query.message.message_id,
        caption=query.message.caption,
        reply_markup=buttons
    )

    await query.answer("Error reported! Thank you.")
