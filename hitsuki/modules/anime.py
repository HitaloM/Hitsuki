# This file is part of Hitsuki (Telegram Bot)

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import aiohttp
from urllib.parse import quote as urlencode

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from hitsuki import bot
from hitsuki.decorator import register
from .utils.disable import disableable_dec
from .utils.message import need_args_dec, get_args_str

# module to get anime and character info
# by t.me/dank_as_fuck (misaki@eagleunion.tk)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:70.0) Gecko/20100101 Firefox/70.0"


@register(cmds='kitsu')
@disableable_dec('kitsu')
async def anime(message): 
   query = get_args_str(message).lower() 
   headers = {"User-Agent": USER_AGENT} 
   query.replace('', '%20') 
   url = f'https://kitsu.io/api/edge/anime?filter%5Btext%5D={urlencode(query)}' 
   session = aiohttp.ClientSession()
   async with session.get(url) as resp:
     a = await resp.json()
     if 'data' in a.keys():
       data = a["data"][0]
       pic = f'{data["attributes"]["coverImage"]["original"] if data["attributes"].get("coverImage", "") else ""}'
       id = f'{a["data"][0]["id"]}'
       info = f'{data["attributes"]["titles"]["en_jp"]}\n'
       info += f'{data["attributes"]["titles"]["ja_jp"]}\n'
       info += f' * Rating: {data["attributes"]["averageRating"]}\n'
       info += f' * Release Date: {data["attributes"]["startDate"]}\n'
       info += f' * End Date: {data["attributes"]["endDate"]}\n'
       info += f' * Status: {data["attributes"]["status"]}\n'
       info += f' * Description: {data["attributes"]["description"]}\n'
       aurl = f'kitsu.io/anime/'+id
       if len(info) > 1024:
         info = info[0:500] + "...."
       link_btn = InlineKeyboardMarkup()
       link_btn.insert(InlineKeyboardButton("Read more", url=aurl))
       if pic:
          await message.reply_photo(pic, caption=info, reply_markup=link_btn)
       else:
          await message.reply_text(info, reply_markup=link_btn)


@register(cmds='mal')
@disableable_dec('mal')
async def manime(message):
   query = get_args_str(message).lower()
   headers = {"User-Agent":USER_AGENT}
   query.replace('', '%20')
   surl = f'https://api.jikan.moe/v3/search/anime?q={urlencode(query)}'
   session = aiohttp.ClientSession()
   async with session.get(surl) as resp:
     a = await resp.json()
     if 'results' in a.keys():   
        pic = f'{a["results"][0]["image_url"]}'
        info = f'{a["results"][0]["title"]}\n'
        info += f' • Airing : {a["results"][0]["airing"]}\n'
        info += f' • Type : {a["results"][0]["type"]}\n'
        info += f' • Episodes : {a["results"][0]["episodes"]}\n'
        info += f' • Score : {a["results"][0]["score"]}\n'
        info += f' • Rated : {a["results"][0]["rated"]}\n'
        info += f' • Synopsis : {a["results"][0]["synopsis"]}\n'
        mlink = f'{a["results"][0]["url"]}\n'
        link_btn = InlineKeyboardMarkup()
        link_btn.insert(InlineKeyboardButton("MyAnimeList Link", url=mlink))
        await message.reply_photo(pic, caption=info, reply_markup=link_btn)
