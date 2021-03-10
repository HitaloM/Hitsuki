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

import time
import html
import httpx
import bs4
import anilist
from jikanpy import AioJikan

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from hitsuki.decorator import register
from .utils.disable import disableable_dec
from .utils.message import get_args_str, need_args_dec


@register(cmds="anime")
@need_args_dec()
@disableable_dec("anime")
async def anilist_anime(message):
    query = get_args_str(message)

    try:
        async with anilist.AsyncClient() as client:
            results = await client.search(query, "anime", 1)
            anime = await client.get(results[0].id, "anime")
    except IndexError:
        return await message.reply(
            "Something went wrong, check your search and try again!"
        )

    if len(anime.description) > 700:
        desc = f"<b>Short description:</b> <i>{anime.description_short}</i>..."
    else:
        desc = f"<b>Description:</b> <i>{anime.description}</i>"

    text = f"<b>{anime.title.romaji}</b> (<code>{anime.title.native}</code>)\n"
    text += f"<b>Type:</b> <code>{anime.format}</code>\n"
    if hasattr(anime, "status"):
        text += f"<b>Status:</b> <code>{anime.status}</code>\n"
    if hasattr(anime, "episodes"):
        text += f"<b>Episodes:</b> <code>{anime.episodes}</code>\n"
    if hasattr(anime, "duration"):
        text += f"<b>Duration:</b> <code>{anime.duration}</code> Por Ep.\n"
    if hasattr(anime.score, "average"):
        text += f"<b>Score:</b> <code>{anime.score.average}</code>\n"
    if hasattr(anime, "genres"):
        text += (
            f"<b>Genres:</b> <code>{', '.join(str(x) for x in anime.genres)}</code>\n"
        )
    if hasattr(anime, "studios"):
        text += (
            f"<b>Studio:</b> <code>{', '.join(str(x) for x in anime.studios)}</code>\n"
        )
    text += f"\n{desc.replace('<br>', '')}"

    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton(text="More Info", url=anime.url)
    )

    try:
        keyboard.add(InlineKeyboardButton(text="Trailer 🎬", url=anime.trailer.url))
    except BaseException:
        pass

    await message.reply_photo(
        photo=f"https://img.anili.st/media/{anime.id}",
        caption=text,
        reply_markup=keyboard,
    )


@register(cmds="airing")
@need_args_dec()
@disableable_dec("airing")
async def anilist_airing(message):
    query = get_args_str(message)

    try:
        async with anilist.AsyncClient() as client:
            results = await client.search(query, "anime", 1)
            anime = await client.get(results[0].id, "anime")
    except IndexError:
        return await message.reply(
            "Something went wrong, check your search and try again!"
        )

    text = f"<b>{anime.title.romaji}</b> (<code>{anime.title.native}</code>)\n"
    text += f"<b>ID:</b> <code>{anime.id}</code>\n"
    text += f"<b>Type:</b> <code>{anime.format}</code>\n"
    if hasattr(anime, "next_airing"):
        text += f"<b>Episode:</b> <code>{anime.next_airing.episode}</code>\n"
        text += f"<b>Airing in:</b> <code>{time.strftime('%H:%M:%S - %d/%m/%Y', time.localtime(anime.next_airing.at))}</code>"
    else:
        text += f"<b>Episode:</b> <code>{anime.episodes}</code>\n"
        text += "<b>Airing in:</b> <code>N/A</code>"

    if hasattr(anime, "banner"):
        await message.reply_photo(photo=anime.banner, caption=text)
    else:
        await message.reply(text)


@register(cmds="manga")
@need_args_dec()
@disableable_dec("manga")
async def anilist_manga(message):
    query = get_args_str(message)

    try:
        async with anilist.AsyncClient() as client:
            results = await client.search(query, "manga", 1)
            manga = await client.get(results[0].id, "manga")
    except IndexError:
        return await message.reply(
            "Something went wrong, check your search and try again!"
        )

    if len(manga.description) > 700:
        desc = f"<b>Short description:</b> <i>{manga.description_short}</i>..."
    else:
        desc = f"<b>Description:</b> <i>{manga.description}</i>"

    text = f"<b>{manga.title.romaji}</b> (<code>{manga.title.native}</code>)\n"
    if hasattr(manga.start_date, "year"):
        text += f"<b>Date:</b> <code>{manga.start_date.year}</code>\n"
    if hasattr(manga, "status"):
        text += f"<b>Status:</b> <code>{manga.status}</code>\n"
    if hasattr(manga, "chapters"):
        text += f"<b>Chapters:</b> <code>{manga.chapters}</code>\n"
    if hasattr(manga, "chapters"):
        text += f"<b>Volumes:</b> <code>{manga.volumes}</code>\n"
    if hasattr(manga.score, "average"):
        text += f"<b>Score:</b> <code>{manga.score.average}</code>\n"
    if hasattr(manga, "genres"):
        text += (
            f"<b>Genres:</b> <code>{', '.join(str(x) for x in manga.genres)}</code>\n"
        )
    text += f"\n{desc.replace('<br>', '')}"

    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton(text="More Info", url=manga.url)
    )

    await message.reply_photo(
        photo=f"https://img.anili.st/media/{manga.id}",
        caption=text,
        reply_markup=keyboard,
    )


@register(cmds="upcoming")
@disableable_dec("upcoming")
async def upcoming(message):
    async with AioJikan() as jikan:
        pass

    upcoming = await jikan.top("anime", page=1, subtype="upcoming")
    await jikan.close()

    upcoming_list = [entry["title"] for entry in upcoming["top"]]
    upcoming_message = ""

    for entry_num in range(len(upcoming_list)):
        if entry_num == 10:
            break
        upcoming_message += f"{entry_num + 1}. {upcoming_list[entry_num]}\n"

    await message.reply(upcoming_message)


async def site_search(message, site: str):
    args = message.text.split(" ", 1)
    more_results = True
    search_query = args[1]

    if site == "kaizoku":
        search_url = f"https://animekaizoku.com/?s={search_query}"
        async with httpx.AsyncClient(http2=True) as http:
            html_text = await http.get(search_url)
        soup = bs4.BeautifulSoup(html_text.text, "html.parser")
        search_result = soup.find_all("h2", {"class": "post-title"})
        await http.aclose()

        if search_result:
            result = f"<b>Search results for</b> <code>{html.escape(search_query)}</code> <b>on</b> <code>AnimeKaizoku</code>: \n"
            for entry in search_result:
                post_link = entry.a["href"]
                post_name = html.escape(entry.text)
                result += f"• <a href='{post_link}'>{post_name}</a>\n"
        else:
            more_results = False
            result = f"<b>No result found for</b> <code>{html.escape(search_query)}</code> <b>on</b> <code>AnimeKaizoku</code>"

    elif site == "kayo":
        search_url = f"https://animekayo.com/?s={search_query}"
        async with httpx.AsyncClient(http2=True) as http:
            html_text = await http.get(search_url)
        soup = bs4.BeautifulSoup(html_text.text, "html.parser")
        search_result = soup.find_all("h2", {"class": "title"})
        await http.aclose()

        result = f"<b>Search results for</b> <code>{html.escape(search_query)}</code> <b>on</b> <code>AnimeKayo</code>: \n"
        for entry in search_result:

            if entry.text.strip() == "Nothing Found":
                result = f"<b>No result found for</b> <code>{html.escape(search_query)}</code> <b>on</b> <code>AnimeKayo</code>"
                more_results = False
                break

            post_link = entry.a["href"]
            post_name = html.escape(entry.text.strip())
            result += f"• <a href='{post_link}'>{post_name}</a>\n"

    buttons = InlineKeyboardMarkup().add(
        InlineKeyboardButton(text="See all results", url=search_url)
    )

    if more_results:
        await message.reply(result, reply_markup=buttons, disable_web_page_preview=True)
    else:
        await message.reply(result)


@register(cmds="kaizoku")
@need_args_dec()
@disableable_dec("kaizoku")
async def kaizoku(message):
    await site_search(message, "kaizoku")


@register(cmds="kayo")
@need_args_dec()
@disableable_dec("kayo")
async def kayo(message):
    await site_search(message, "kayo")


__mod_name__ = "Anime"

__help__ = """
Get information about anime, manga or anime characters.

<b>Available commands:</b>
- /anime (anime): returns information about the anime.
- /manga (manga): returns information about the manga.
- /airing (anime): returns anime airing info.
- /kaizoku (anime): search an anime on animekaizoku.com
- /kayo (anime): search an anime on animekayo.com
- /upcoming: returns a list of new anime in the upcoming seasons.
"""
