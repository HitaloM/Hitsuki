import re

from telethon import events
from aiogram.dispatcher.handler import SkipHandler
from aiogram import types

from sophie_bot import BOT_USERNAME, CONFIG, tbot, dp

ALLOW_F_COMMANDS = CONFIG["advanced"]["allow_forwards_commands"]
ALLOW_COMMANDS_FROM_EXC = CONFIG["advanced"]["allow_commands_with_!"]
BLOCK_GBANNED_USERS = CONFIG["advanced"]["block_gbanned_users"]

REGISTRED_COMMANDS = []


def t_command(command, arg="", word_arg="", additional="", **kwargs):
    REGISTRED_COMMANDS.append(command)

    def decorator(func):

        if 'forwards' not in kwargs:
            kwargs['forwards'] = ALLOW_F_COMMANDS

        if ALLOW_COMMANDS_FROM_EXC is True:
            P = '[/!]'
        else:
            P = '/'

        if arg is True:
            cmd = "^{P}(?i:{0}|{0}@{1})(?: |$)(.*){2}".format(command, BOT_USERNAME, additional,
                                                              P=P)
        elif word_arg is True:
            cmd = "^{P}(?i:{0}|{0}@{1})(?: |$)(\S*){2}".format(command, BOT_USERNAME, additional,
                                                               P=P)
        else:
            cmd = "^{P}(?i:{0}|{0}@{1})$".format(command, BOT_USERNAME, additional, P=P)

        tbot.add_event_handler(func, events.NewMessage(incoming=True, pattern=cmd, **kwargs))
        tbot.add_event_handler(func, events.MessageEdited(incoming=True, pattern=cmd, **kwargs))
    return decorator


def command(command, allow_edited=True, **kwargs):
    REGISTRED_COMMANDS.append(command)

    def decorator(func):
        if ALLOW_COMMANDS_FROM_EXC is True:
            P = '[/!]'
        else:
            P = '/'

        if 'not_gbanned' not in kwargs and BLOCK_GBANNED_USERS is True:
            kwargs['not_gbanned'] = True

        if 'not_forwarded' not in kwargs and ALLOW_F_COMMANDS is False:
            kwargs['not_forwarded'] = True

        cmd = "^{0}(?i:{1}|{1}@{2})(?: |$)".format(P, command, BOT_USERNAME)

        async def new_func(*args, **def_kwargs):
            if 'allow_kwargs' not in kwargs:
                def_kwargs = dict()
            await func(*args, **def_kwargs)
            raise SkipHandler()

        dp.register_message_handler(new_func, regexp=cmd, **kwargs)
        if allow_edited is True:
            dp.register_edited_message_handler(new_func, regexp=cmd, **kwargs)
    return decorator


def cust_command(*args, **kwargs):
    def decorator(func):
        tbot.add_event_handler(func, events.NewMessage(*args, **kwargs))
        tbot.add_event_handler(func, events.MessageEdited(*args, **kwargs))
    return decorator


def CallBackQuery(data, compile=True):
    def decorator(func):
        if compile is True:
            tbot.add_event_handler(func, events.CallbackQuery(data=re.compile(data)))
        else:
            tbot.add_event_handler(func, events.CallbackQuery(data=data))
    return decorator


def BotDo():
    def decorator(func):
        tbot.add_event_handler(func, events.NewMessage())
        tbot.add_event_handler(func, events.MessageEdited())
    return decorator


def AioBotDo(**kwargs):
    def cascade_measage_handler(func):

        async def new_func(*args, **def_kwargs):
            if 'allow_kwargs' not in kwargs:
                def_kwargs = dict()
            await func(*args, **def_kwargs)
            raise SkipHandler()

        dp.register_message_handler(new_func, **kwargs)
        return new_func
    return cascade_measage_handler


def AioWelcome():
    def cascade_measage_handler(func):

        async def new_func(*args, **kwargs):
            await func(*args, **kwargs)
            raise SkipHandler()

        dp.register_message_handler(new_func, content_types=types.ContentTypes.NEW_CHAT_MEMBERS)
        return new_func
    return cascade_measage_handler


def insurgent():
    def decorator(func):
        tbot.add_event_handler(func, events.NewMessage(incoming=True))
        tbot.add_event_handler(func, events.MessageEdited(incoming=True))
    return decorator


def StrictCommand(cmd):
    def decorator(func):
        tbot.add_event_handler(func, events.NewMessage(incoming=True, pattern=cmd))
        tbot.add_event_handler(func, events.MessageEdited(incoming=True, pattern=cmd))
    return decorator


def ChatAction():
    def decorator(func):
        tbot.add_event_handler(func, events.ChatAction)
    return decorator


def RawAction():
    def decorator(func):
        tbot.add_event_handler(func, events.Raw)
    return decorator
