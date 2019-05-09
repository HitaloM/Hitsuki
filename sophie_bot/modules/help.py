from sophie_bot.events import flood_limit, register

from telethon import custom


@register(incoming=True, pattern="^[/!]start help$")
async def event(event):

    res = flood_limit(event.chat_id, 'starthelp')
    if res == 'EXIT':
        return
    elif res is True:
        await event.reply('**Flood detected! **\
Please wait 3 minutes before using this command')
        return

    text = "If you are seeing that mean help is working"
    await event.reply(text)


@register(incoming=True, pattern="^[/!]help$")
async def help(event):

    res = flood_limit(event.chat_id, 'help')
    if res == 'EXIT':
        return
    elif res is True:
        await event.reply('**Flood detected! **\
Please wait 3 minutes before using this command')
        return

    if not event.from_id == event.chat_id:
        text = "Contact me in PM for help"
        inline = [[custom.Button.url('Click me for help!', 'https://t.me/rSophieBot?start=help')]]
        await event.reply(text, buttons=inline)
        return
    text = "\n__yea__ \n**yea** \n`yea`"
    inline = [[custom.Button.url('Click me for help!',
              'https://t.me/rSophieBot?start=help')]]
    await event.reply(text, buttons=inline)
