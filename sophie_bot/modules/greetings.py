from sophie_bot import bot
from telethon import events


@bot.on(events.ChatAction)
async def handler(event):
    print(event.user_joined)
    if event.user_joined is not True:
        return
    await event.reply("TEST")