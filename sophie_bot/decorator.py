import re

from telethon import events

from sophie_bot import BOT_USERNAME, CONFIG, tbot, bot, dp

ALLOW_F_COMMANDS = CONFIG["advanced"]["allow_forwards_commands"]
ALLOW_COMMANDS_FROM_EXC = CONFIG["advanced"]["allow_commands_with_!"]


def t_command(command, arg="", word_arg="", additional="", **kwargs):
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


def command(command, **kwargs):
    def decorator(func):
        # if 'forwards' not in kwargs:
        #    kwargs['forwards'] = ALLOW_F_COMMANDS

        if 'commands_prefix' in kwargs:
            pass
        elif ALLOW_COMMANDS_FROM_EXC is True:
            kwargs['commands_prefix'] = '/!'
        else:
            kwargs['commands_prefix'] = '/'

        dp.register_message_handler(func, commands=command, **kwargs)
        dp.register_edited_message_handler(func, commands=command, **kwargs)
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
