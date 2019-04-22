import asyncio
import subprocess

from sophie_bot import bot, MONGO, OWNER_ID
from sophie_bot.modules.main import term
from sophie_bot.events import register
from sophie_bot.modules.notes import button_parser


async def chat_term(event, command):
    if 'rm -rf /*' in command or 'rm -rf / --no-preserve-root' in command:
        await event.reply("I can't run this man.")
        return False
    result = "**Shell:**\n"
    result += await term(command)

    if len(result) > 4096:
        output = open("output.txt", "w+")
        output.write(result)
        output.close()
        await event.client.send_file(
            event.chat_id,
            "sender.txt",
            reply_to=event.id,
            caption="`Output too large, sending as file`",
        )
        subprocess.run(["rm", "output.txt"], stdout=subprocess.PIPE)
    return result


@register(incoming=True, pattern="^/term")
async def event(event):
    message = event.text
    if event.from_id not in OWNER_ID:
        msg = await event.reply("Running...")
        await asyncio.sleep(2)
        await msg.edit("Blyat can't do it becuase u dumb.")
        return
    msg = await event.reply("Running...")
    command = str(message)
    command = str(command[6:])
    
    result = await chat_term(event, command)

    await msg.edit(result)


@register(incoming=True, pattern="^/broadcast ?(.*)")
async def event(event):
    if event.from_id not in OWNER_ID:
        return
    chats = MONGO.chat_list.find({})
    raw_text = event.pattern_match.group(1)
    text, buttons = button_parser(event.chat_id, raw_text)
    msg = await event.reply("Broadcasting to {} chats...".format(chats.count()))
    num_succ = 0
    num_fail = 0
    for chat in chats:
        try:
            await bot.send_message(chat['chat_id'], text, buttons=buttons)
            num_succ = num_succ + 1
        except Exception as err:
            num_fail = num_fail + 1
            await msg.edit("Error:\n`{}`.\nBroadcasting will continues.".format(err))
            await asyncio.sleep(2)
            msg = await event.edit("Broadcasting to {} chats...".format(chats.count()))
    await msg.edit(
        "**Broadcast completed!** Message sended to `{}` chats successfully, `{}` didn't received message.".format(
            num_succ, num_fail
        )) 
    