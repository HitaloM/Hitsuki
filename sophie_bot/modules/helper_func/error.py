import sys
import io
import traceback
import ujson
import datetime

from time import gmtime, strftime

from aiogram import types

from sophie_bot import DEBUG_MODE, mongodb, dp, logger, bot
from sophie_bot.modules.helper_func.term import term


@dp.errors_handler()
async def all_errors_handler(message, dp):
    await report_error(message)


async def report_error(event, telethon=False):
    if telethon is True:
        msg = event
        chat_id = msg.chat_id
        lib = 'Telethon'
    else:
        msg = event.message
        chat_id = msg.chat.id
        lib = 'Aiogram'

    date = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    logger.error("Error: " + date)
    logger.error("Lib: " + lib)

    if telethon is True:
        logger.error(traceback.format_exc())

    if DEBUG_MODE is True:
        await msg.reply(str(sys.exc_info()[1]))
        return

    new = {
        'error': str(sys.exc_info()[1]),
        'date': datetime.datetime.now()
    }
    mongodb.errors.insert_one(new)

    text = "<b>Sorry, I encountered a error!</b>\n"
    link = "<a href=\"https://t.me/YanaBotGroup\">Sophie support chat</a>"
    text += f"If you wanna you can report it - just forward this file to {link}.\n"
    text += "I won't log anything except the fact of error and date\n"

    ftext = "Sophie error log file."
    ftext += "\n______________________\n"
    ftext += "\nNotice:\nThis file uploaded ONLY here, we logged only fact of error and date, "
    ftext += "we respect your privacy, you may not report this error if you've "
    ftext += "any confidential data here, noone will see your data\n\n"
    ftext += "\nDate: " + date
    ftext += "\nLib: " + lib
    ftext += "\nGroup ID: " + str(chat_id)
    ftext += "\nSender ID: " + str(msg.from_user.id if lib == "Aiogram" else msg.from_id)
    ftext += "\n\nRaw update text:\n"
    ftext += str(event)
    ftext += "\n\nFormatted update text:\n"
    ftext += str(ujson.dumps(msg, indent=2))
    ftext += "\n\nTraceback info:\n"
    ftext += str(traceback.format_exc())
    ftext += "\n\nError text:\n"
    ftext += str(sys.exc_info()[1])

    command = "git log --pretty=format:\"%an: %s\" -5"
    ftext += "\n\n\nLast 5 commits:\n"
    ftext += await term(command)

    await bot.send_document(
        chat_id,
        types.InputFile(io.StringIO(ftext), filename="Error.txt"),
        caption=text,
        reply_to_message_id=msg.message_id if lib == "Aiogram" else msg.message.id
    )

    return
