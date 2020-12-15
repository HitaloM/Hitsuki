from aiogram import types
from hitsuki import bot
from hitsuki.decorator import register
from .utils.disable import disableable_dec
from PIL import Image
from math import floor
import os

download_path = "/"
class Stickers:
    def __init__(self, owner_id: int, sticker_data) -> None:
        self.owner_id = owner_id
        self.sticker_data = sticker_data
        self.is_animated = sticker_data["is_animated"]

        try: 
            self.emoji = sticker_data["emoji"]
        except:
            self.emoji = "🤔"
        

    async def download_sticker(self) -> None:
        file_destination = f"{download_path}{self.sticker_data['thumb']['file_unique_id']}.{'tgs' if self.is_animated else 'png'}" 
        file = await bot.get_file(self.sticker_data["thumb"]["file_id"])
        await bot.download_file(file["file_path"], file_destination)

        self.file_destination = file_destination
    
    async def available_sticker_set(self, user_data) -> str:
        packnum = 1
        sticker_set_type = 'ssA' if self.is_animated else 'ss'
        self.packname = f"{user_data['id']}_by_hitsuki_bot"
        self.user_data = user_data
        while True:
            sticker_url = f"{sticker_set_type}{packnum}_{self.packname}"
            try: 
                sticker_set = await bot.get_sticker_set(sticker_url)
                if len(sticker_set["stickers"]) < 120 and self.is_animated == False:
                    self.sticker_url = sticker_url
                    await self.upload_sticker_to_set(self.is_animated, self.user_data, self.sticker_url, self.emoji, self.file_destination)
                    return sticker_url

                elif len(sticker_set["stickers"]) < 50 and self.is_animated == True:
                    self.sticker_url = sticker_url
                    await self.upload_sticker_to_set(self.is_animated, self.user_data, self.sticker_url, self.emoji, self.file_destination)
                    return sticker_url
                else:
                    pass

                packnum += 1
            except:
                self.sticker_url = sticker_url
                if await self.create_sticker_set(self.is_animated, self.user_data, self.sticker_url, self.emoji, self.file_destination):
                    return sticker_url
    @staticmethod
    async def create_sticker_set(is_animated, user_data, sticker_url, emoji, file_destination):
        if is_animated == False:
            await bot.add_sticker_to_set(
                user_id = user_data["id"],
                name = sticker_url,
                emojis = emoji,
                png_sticker = types.InputFile(file_destination))
        else:
            await bot.add_sticker_to_set(
                user_id = user_data["id"],
                name = sticker_url,
                emojis = emoji,
                tgs_sticker = types.InputFile(file_destination))
    @staticmethod
    async def upload_sticker_to_set(is_animated, user_data, sticker_url, emoji, file_destination):
        if is_animated == False:
            await bot.add_sticker_to_set(
                user_id = user_data["id"],
                name = sticker_url,
                emojis = emoji,
                png_sticker = types.InputFile(file_destination))
        else:
            await bot.add_sticker_to_set(
                user_id = user_data["id"],
                name = sticker_url,
                emojis = emoji,
                tgs_sticker = types.InputFile(file_destination))

@register(cmds='kang')
@disableable_dec('kang')
async def kang(message: types.Message):
    
    try:
        sticker_data = message["reply_to_message"]["sticker"]
    except:
        await message.reply("Kang need an reply")
        return False

    sticker = Stickers(message["from"]["id"], sticker_data)
    if sticker_data["is_animated"] == True:
        await message.reply("Kang animated stickers aren't available yet! Sorry")
        return False
        
    await sticker.download_sticker()
    answer = await message.answer("Downloading document...")

    image = Image.open(sticker.file_destination)
    
    sides = floor((512/image.height) * image.width), floor((512/image.width) * image.height)
    if image.width < 512 or image.height < 512:
        out = image.resize(sides, 0)
        out.thumbnail((512, 512), 0)
        out.save(sticker.file_destination, "PNG")
    
    answer = await bot.edit_message_text(
        text="<strong>Download finished!</strong>",
        chat_id=message["chat"]["id"],
        message_id=answer["message_id"],
        parse_mode='html')

    await sticker.available_sticker_set(message["from"])
    await bot.edit_message_text("Sticker added succesfully to <a href='{packname}'>pack</a>\nEmoji: {emoji}".format(
        packname=sticker.sticker_url, emoji=sticker.emoji), parse_mode='html',
        chat_id=message["chat"]["id"], message_id=answer["message_id"])
    
    os.remove(sticker.file_destination)

