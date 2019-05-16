from sophie_bot import BOT_NICK, bot

from telethon import events


def register(**args):
    pattern = args.get('pattern', None)

    if pattern is not None and not pattern.startswith('(?i)'):
        args['pattern'] = '(?i)' + pattern

    def decorator(func):
        bot.add_event_handler(func, events.NewMessage(**args))
        bot.add_event_handler(func, events.MessageEdited(**args))
        return func

    return decorator


def command(command, arg=False, additional=""):
    def decorator(func):
        if arg is True:
            cmd = "^[/!](?:{0}|{0}@{1})(?: |$)(.*){2}".format(command, BOT_NICK, additional)
        else:
            cmd = "^[/!](?:{0}|{0}@{1})$".format(command, BOT_NICK, additional)
        bot.add_event_handler(func, events.NewMessage(incoming=True, pattern=cmd))
        bot.add_event_handler(func, events.MessageEdited(incoming=True, pattern=cmd))
    return decorator
