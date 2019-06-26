from sophie_bot import decorator, mongodb
from sophie_bot.modules.connections import t_connection
from sophie_bot.modules.helper_func.flood import t_flood_limit_dec
from sophie_bot.modules.language import t_get_strings_dec
from sophie_bot.modules.users import t_user_admin_dec

global DISABLABLE_COMMANDS
DISABLABLE_COMMANDS = []


@decorator.command("disablable")
@t_flood_limit_dec("disablable")
async def list_disablable(event):
    text = "**Disablable commands are:**\n"
    for command in DISABLABLE_COMMANDS:
        text += f"* `{command}`\n"
    await event.reply(text)


@decorator.command("disable ?(.*)")
@t_user_admin_dec
@t_connection(admin=True, only_in_groups=True)
@t_get_strings_dec("disable")
async def disable_command(event, strings, status, chat_id, chat_title):
    if not event.pattern_match.group(1):
        await event.reply(strings["wot_to_disable"])
        return
    cmd = event.pattern_match.group(1).lower()
    if cmd[0] == '/' or cmd[0] == '!':
        cmd = cmd[1:]
    if cmd not in DISABLABLE_COMMANDS:
        await event.reply(strings["wot_to_disable"])
        return
    new = {
        "chat_id": chat_id,
        "command": cmd
    }
    old = mongodb.disabled_cmds.find_one(new)
    if old:
        await event.reply(strings['already_disabled'])
        return
    mongodb.disabled_cmds.insert_one(new)
    await event.reply(strings["disabled"].format(cmd, chat_title))


@decorator.command("enable ?(.*)")
@t_user_admin_dec
@t_connection(admin=True, only_in_groups=True)
@t_get_strings_dec("disable")
async def enable_command(event, strings, status, chat_id, chat_title):
    if not event.pattern_match.group(1):
        await event.reply(strings["wot_to_enable"])
        return
    cmd = event.pattern_match.group(1).lower()
    if cmd[0] == '/' or cmd[0] == '!':
        cmd = cmd[1:]
    if cmd not in DISABLABLE_COMMANDS:
        await event.reply(strings["wot_to_enable"])
        return
    old = mongodb.disabled_cmds.find_one({
        "chat_id": chat_id,
        "command": cmd
    })
    if not old:
        await event.reply(strings["already_enabled"])
        return
    mongodb.disabled_cmds.delete_one({'_id': old['_id']})
    await event.reply(strings["enabled"].format(cmd))


def t_disablable_dec(command):
    if command not in DISABLABLE_COMMANDS:
        DISABLABLE_COMMANDS.append(command)

    def wrapped(func):
        async def wrapped_1(event, *args, **kwargs):
            check = mongodb.disabled_cmds.find_one({
                "chat_id": event.chat_id,
                "command": command
            })
            if check:
                return
            return await func(event, *args, **kwargs)
        return wrapped_1
    return wrapped
