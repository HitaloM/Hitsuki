from sophie_bot import decorator, mongodb
from sophie_bot.modules.connections import connection
from sophie_bot.modules.helper_func.flood import flood_limit_dec
from sophie_bot.modules.language import get_strings_dec
from sophie_bot.modules.users import user_admin_dec

global DISABLABLE_COMMANDS
DISABLABLE_COMMANDS = []


@decorator.command("disablable")
@flood_limit_dec("disablable")
@get_strings_dec("disable")
async def list_disablable(message, strings, **kwargs):
    text = strings['disablable']
    for command in DISABLABLE_COMMANDS:
        text += f"* <code>/{command}</code>\n"
    await message.reply(text)


@decorator.command("disabled")
@flood_limit_dec("disabled")
@connection(only_in_groups=True)
@get_strings_dec("disable")
async def list_disabled(message, strings, status, chat_id, chat_title, **kwargs):
    text = strings['disabled_list'].format(chat_name=chat_title)
    commands = mongodb.disabled_cmds.find({'chat_id': chat_id})
    for command in commands:
        text += f"* <code>/{command}</code>\n"
    await message.reply(text)


@decorator.command("disable")
@user_admin_dec
@connection(admin=True, only_in_groups=True)
@get_strings_dec("disable")
async def disable_command(message, strings, status, chat_id, chat_title, **kwargs):
    if len(message.text.split(" ")) <= 1:
        await message.reply(strings["wot_to_disable"])
        return
    cmd = message.text.split(" ")[1].lower()
    if cmd[0] == '/' or cmd[0] == '!':
        cmd = cmd[1:]
    if cmd not in DISABLABLE_COMMANDS:
        await message.reply(strings["wot_to_disable"])
        return
    new = {
        "chat_id": chat_id,
        "command": cmd
    }
    old = mongodb.disabled_cmds.find_one(new)
    if old:
        await message.reply(strings['already_disabled'])
        return
    mongodb.disabled_cmds.insert_one(new)
    await message.reply(strings["disabled"].format(
        cmd=cmd, chat_name=chat_title))


@decorator.command("enable")
@user_admin_dec
@connection(admin=True, only_in_groups=True)
@get_strings_dec("disable")
async def enable_command(message, strings, status, chat_id, chat_title, **kwargs):
    if len(message.text.split(" ")) <= 1:
        await message.reply(strings["wot_to_enable"])
        return
    cmd = message.text.split(" ")[1].lower()
    if cmd[0] == '/' or cmd[0] == '!':
        cmd = cmd[1:]
    if cmd not in DISABLABLE_COMMANDS:
        await message.reply(strings["wot_to_enable"])
        return
    old = mongodb.disabled_cmds.find_one({
        "chat_id": chat_id,
        "command": cmd
    })
    if not old:
        await message.reply(strings["already_enabled"])
        return
    mongodb.disabled_cmds.delete_one({'_id': old['_id']})
    await message.reply(strings["enabled"].format(
        cmd=cmd, chat_name=chat_title))


def disablable_dec(command):
    if command not in DISABLABLE_COMMANDS:
        DISABLABLE_COMMANDS.append(command)

    def wrapped(func):
        async def wrapped_1(event, *args, **kwargs):

            if hasattr(event, 'chat_id'):
                chat_id = event.chat_id
            elif hasattr(event, 'chat'):
                chat_id = event.chat.id

            check = mongodb.disabled_cmds.find_one({
                "chat_id": chat_id,
                "command": command
            })
            if check:
                return
            return await func(event, *args, **kwargs)
        return wrapped_1
    return wrapped
