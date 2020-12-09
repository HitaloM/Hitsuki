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

import requests
import rapidjson as json

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from hitsuki.decorator import register
from .utils.disable import disableable_dec

url = 'https://graphql.anilist.co'


def shorten(description, info='anilist.co'):
    ms_g = ""
    if len(description) > 700:
        description = description[0:500] + '...'
        ms_g += f"\n<b>Description</b>: <i>{description}</i> <a href='{info}'>Read More</a>"
    else:
        ms_g += f"\n<b>Description</b>: <i>{description}</i>"
    return (
        ms_g.replace("<br>", "")
        .replace("</br>", "")
        .replace("<i>", "")
        .replace("</i>", "")
    )


def t(milliseconds: int) -> str:
    """Inputs time in milliseconds, to get beautified time,
    as string"""
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + " Days, ") if days else "") + \
        ((str(hours) + " Hours, ") if hours else "") + \
        ((str(minutes) + " Minutes, ") if minutes else "") + \
        ((str(seconds) + " Seconds, ") if seconds else "") + \
        ((str(milliseconds) + " ms, ") if milliseconds else "")
    return tmp[:-2]


airing_query = '''
    query ($id: Int,$search: String) {
      Media (id: $id, type: ANIME,search: $search) {
        id
        episodes
        title {
          romaji
          english
          native
        }
        siteUrl
        nextAiringEpisode {
           airingAt
           timeUntilAiring
           episode
        }
      }
    }
    '''

fav_query = """
query ($id: Int) {
      Media (id: $id, type: ANIME) {
        id
        title {
          romaji
          english
          native
        }
     }
}
"""

anime_query = '''
   query ($id: Int,$search: String) {
      Media (id: $id, type: ANIME,search: $search) {
        id
        idMal
        title {
          romaji
          english
          native
        }
        description (asHtml: false)
        startDate{
            year
          }
          episodes
          season
          type
          format
          status
          duration
          siteUrl
          studios{
              nodes{
                   name
              }
          }
          trailer{
               id
               site 
               thumbnail
          }
          averageScore
          genres
          bannerImage
      }
    }
'''
character_query = """
    query ($query: String) {
        Character (search: $query) {
               id
               name {
                     first
                     last
                     full
               }
               siteUrl
               favourites
               image {
                        large
               }
               description
        }
    }
"""

manga_query = """
query ($id: Int,$search: String) {
      Media (id: $id, type: MANGA,search: $search) {
        id
        title {
          romaji
          english
          native
        }
        description (asHtml: false)
        startDate{
            year
          }
          type
          format
          status
          siteUrl
          averageScore
          genres
          bannerImage
      }
    }
"""


@register(cmds='airing')
@disableable_dec('airing')
async def anime_airing(message):
    search_str = message.text.split(' ', 1)
    if len(search_str) == 1:
        await message.reply('Provide anime name!')
        return

    variables = {'search': search_str[1]}
    response = requests.post(
        url, json={'query': airing_query, 'variables': variables}).json()['data']['Media']
    ms_g = f"<b>Name</b>: <b>{response['title']['romaji']}</b>(<code>{response['title']['native']}</code>)\n<b>ID</b>: <code>{response['id']}</code>"
    if response['nextAiringEpisode']:
        airing_time = response['nextAiringEpisode']['timeUntilAiring'] * 1000
        airing_time_final = t(airing_time)
        ms_g += f"\n<b>Episode</b>: <code>{response['nextAiringEpisode']['episode']}</code>\n<b>Airing In</b>: <code>{airing_time_final}</code>"
    else:
        ms_g += f"\n<b>Episode</b>: <code>{response['episodes']}</code>\n<b>Status</b>: <code>N/A</code>"
    await message.reply(ms_g)


@register(cmds='anime')
@disableable_dec('anime')
async def anime_search(message):
    search = message.text.split(' ', 1)
    if len(search) == 1:
        await message.reply('Provide anime name!')
        return
    else:
        search = search[1]
    variables = {'search': search}
    json = requests.post(url, json={'query': anime_query, 'variables': variables}).json()[
        'data'].get('Media', None)
    if json:
        msg = f"<b>{json['title']['romaji']}</b>(<code>{json['title']['native']}</code>)\n<b>Type</b>: {json['format']}\n<b>Status</b>: {json['status']}\n<b>Episodes</b>: {json.get('episodes', 'N/A')}\n<b>Duration</b>: {json.get('duration', 'N/A')} Per Ep.\n<b>Score</b>: {json['averageScore']}\n<b>Genres</b>: <code>"
        for x in json['genres']:
            msg += f"{x}, "
        msg = msg[:-2] + '</code>\n'
        msg += "<b>Studios</b>: <code>"
        for x in json['studios']['nodes']:
            msg += f"{x['name']}, "
        msg = msg[:-2] + '</code>\n'
        info = json.get('siteUrl')
        trailer = json.get('trailer', None)
        if trailer:
            trailer_id = trailer.get('id', None)
            site = trailer.get('site', None)
            if site == "youtube":
                trailer = 'https://youtu.be/' + trailer_id
        description = json.get(
            'description', 'N/A').replace('<i>', '').replace('</i>', '').replace('<br>', '')
        msg += shorten(description, info)
        image = info.replace('anilist.co/anime/', 'img.anili.st/media/')
        if trailer:
            buttons = InlineKeyboardMarkup().add(InlineKeyboardButton(text="More Info", url=info),
                                                 InlineKeyboardButton(text="Trailer 🎬", url=trailer))
        else:
            buttons = InlineKeyboardMarkup().add(
                InlineKeyboardButton(text="More Info", url=info))

        if image:
            try:
                await message.reply_photo(image, caption=msg, reply_markup=buttons)
            except:
                msg += f" [〽️]({image})"
                await message.reply(msg)
        else:
            await message.reply(msg)


@register(cmds='character')
@disableable_dec('character')
async def character_search(message):
    search = message.text.split(' ', 1)
    if len(search) == 1:
        await message.reply('Provide character name!')
        return
    search = search[1]
    variables = {'query': search}
    json = requests.post(url, json={'query': character_query, 'variables': variables}).json()[
        'data'].get('Character', None)
    if json:
        ms_g = f"<b>{json.get('name').get('full')}</b>(<code>{json.get('name').get('native')}</code>)\n"
        description = (f"{json['description']}").replace('__', '')
        site_url = json.get('siteUrl')
        ms_g += shorten(description, site_url)
        image = json.get('image', None)
        if image:
            image = image.get('large')
            await message.reply_photo(image, caption=ms_g)
        else:
            await message.reply(ms_g)


@register(cmds='manga')
@disableable_dec('manga')
async def manga_search(message):
    search = message.text.split(' ', 1)
    if len(search) == 1:
        await message.reply('Provide manga name!')
        return
    search = search[1]
    variables = {'search': search}
    json = requests.post(url, json={'query': manga_query, 'variables': variables}).json()[
        'data'].get('Media', None)
    ms_g = ''
    if json:
        title, title_native = json['title'].get(
            'romaji', False), json['title'].get('native', False)
        start_date, status, score = json['startDate'].get('year', False), json.get(
            'status', False), json.get('averageScore', False)
        if title:
            ms_g += f"<b>{title}</b>"
            if title_native:
                ms_g += f"(<code>{title_native}</code>)"
        if start_date:
            ms_g += f"\n<b>Start Date</b> - <code>{start_date}</code>"
        if status:
            ms_g += f"\n<b>Status</b> - <code>{status}</code>"
        if score:
            ms_g += f"\n<b>Score</b> - <code>{score}</code>"
        ms_g += '\n<b>Genres</b> - '
        for x in json.get('genres', []):
            ms_g += f"{x}, "
        ms_g = ms_g[:-2]

        image = json.get("bannerImage", False)
        ms_g += (f"\n<i>{json.get('description', None)}</i>").replace('<br>', '').replace("</br>", "")
        if image:
            try:
                await message.reply_photo(image, caption=ms_g)
            except:
                ms_g += f" [〽️]({image})"
                await message.reply(ms_g)
        else:
            await message.reply(ms_g)
