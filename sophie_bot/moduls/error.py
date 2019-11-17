import random
import sys

from sophie_bot import dp, bot


RANDOM_ERROR_TITLES = [
    "IT'S A CREEEPER!!!1",
    "BOOM!",
    "It was funny, but I go away.",
    "Don't look at me 😒",
    "Someone again messed me",
    ":( Your PC ran into a problem and needs to restart...",
    "Hello Microsoft?",
    "YEY NEW ERROR! Lets spam to developers.",
    "It's hurt me",
    "I'm crashed, but you still can use /cat command",
    "PIX ME SOME1 PLOX",
    "*Blue screen of death*",
    "It's crash time!"
]


@dp.errors_handler()
async def all_errors_handler(message, dp):
    if 'callback_query' in message:
        msg = message.callback_query.message
    else:
        msg = message.message
    chat_id = msg.chat.id
    error = str(sys.exc_info()[1])
    text = "<b>Sorry, I encountered a error!</b>\n"
    #text += random.choice(RANDOM_ERROR_TITLES)
    text += '<code>%s</code>' % error
    await bot.send_message(chat_id, text, reply_to_message_id=msg.message_id)
