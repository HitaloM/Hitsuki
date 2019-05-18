import re
from sophie_bot import BOT_NICK, bot

from telethon import events


def command(command, arg=False, additional=""):
    def decorator(func):
        if arg is True:
            cmd = "^[/!](?:{0}|{0}@{1})(?: |$)(.*){2}".format(command, BOT_NICK, additional)
        else:
            cmd = "^[/!](?:{0}|{0}@{1})$".format(command, BOT_NICK, additional)
        bot.add_event_handler(func, events.NewMessage(incoming=True, pattern=cmd))
        bot.add_event_handler(func, events.MessageEdited(incoming=True, pattern=cmd))
    return decorator


def CallBackQuery(data, compile=True):
    def decorator(func):
        if compile is True:
            bot.add_event_handler(func, events.CallbackQuery(data=re.compile(data)))
        else:
            bot.add_event_handler(func, events.CallbackQuery(data=data))
    return decorator


def BotDo():
    def decorator(func):
        bot.add_event_handler(func, events.NewMessage())
        bot.add_event_handler(func, events.MessageEdited())
    return decorator


def insurgent():
    def decorator(func):
        bot.add_event_handler(func, events.NewMessage(incoming=True))
        bot.add_event_handler(func, events.MessageEdited(incoming=True))
    return decorator


def StrictCommand(cmd):
    def decorator(func):
        bot.add_event_handler(func, events.NewMessage(incoming=True, pattern=cmd))
        bot.add_event_handler(func, events.MessageEdited(incoming=True, pattern=cmd))
    return decorator


def ChatAction():
    def decorator(func):
        bot.add_event_handler(func, events.ChatAction)
    return decorator
