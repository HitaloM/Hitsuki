import random
import string
import asyncio

from sophie_bot import MONGO, bot
from sophie_bot.events import flood_limit, register
from sophie_bot.modules.notes import button_parser


@register(incoming=True, pattern="^/createchannel (.?)")
async def event(event):
    res = flood_limit(event.chat_id, 'notes')
    if res == 'EXIT':
        return
    elif res is True:
        await event.reply('**Flood detected! **\
Please wait 3 minutes before using this command')
        return

    name = event.message.raw_text.split(" ", 2)[1]
    channel_id = rand_string()
    MONGO.channellist.insert_one({
        'name': name,
        'owner': event.from_id,
        'id': channel_id,
        'chats': []
    })
    await event.reply(
        "Channel **{}** created, id - `{}` connect chat to this channel with `/channelconnect {}`.".format(
            name, channel_id, channel_id
        ))


@register(incoming=True, pattern="^/channels")
async def event(event):
    res = flood_limit(event.chat_id, 'notes')
    if res == 'EXIT':
        return
    elif res is True:
        await event.reply('**Flood detected! **\
Please wait 3 minutes before using this command')
        return

    channels = MONGO.channellist.find({'owner': event.from_id})
    text = "**Your channels:**\n"
    for channel in channels:
        text += '* {} (`{}`)\n'.format(channel['name'], channel['id'])
    await event.reply(text)


@register(incoming=True, pattern="^/channelconnect (.?)")
async def event(event):
    channel_id = event.message.raw_text.split(" ", 2)[1]
    chat_id = event.chat_id
    print(channel_id)
    old = MONGO.channellist.find_one({'id': channel_id})
    if not old:
        await event.reply("I can't find this channel..")
        return
    if chat_id in old['chats']:
        await event.reply("This chat already in channel..")
        return
    new = old['chats']
    new += [chat_id]
    MONGO.channellist.update_one({"_id": old["_id"]}, {"$set": {"chats": new}})
    await event.reply("Chat added!")
    

@register(incoming=True, pattern="^/createnews (.?)")
async def event(event):
    raw_args = event.message.raw_text.split(" ", 2)
    print(raw_args)
    channel_id = raw_args[1]
    print(channel_id)
    text, buttons = button_parser(event.chat_id, raw_args[2])
    if len(buttons) == 0:
        buttons = None
    channel = MONGO.channellist.find_one({'id': channel_id})
    if not channel:
        await event.reply("I can't find this channel.")
    if not event.from_id == channel['owner']:
        await event.reply("You don't have right do it")
        return
    chats = channel['chats']
    msg = await event.reply("Sending message to {} chats...".format(len(chats)))
    num_succ = 0
    num_fail = 0
    for chat in chats:
        try:
            print(chat)
            await bot.send_message(chat, text, buttons=buttons)
            num_succ = num_succ + 1
        except Exception as err:
            num_fail = num_fail + 1
            await msg.edit("Error:\n`{}`.\nBroadcasting will continues.".format(err))
            await asyncio.sleep(2)
            await msg.edit("Broadcasting to {} chats...".format(len(chats)))
    await msg.edit(
        "**News created!** Message sended to `{}` chats successfully, `{}` didn't received message.".format(
            num_succ, num_fail
        )) 


def rand_string(stringLength=8):
    """Generate a random string of fixed length """
    letters= string.ascii_lowercase
    return ''.join(random.sample(letters,stringLength))