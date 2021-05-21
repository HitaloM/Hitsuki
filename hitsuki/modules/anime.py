# Copyright (C) 2021 HitaloSama.
# Copyright (C) 2019 Aiogram.
#
# This file is part of Hitsuki (Telegram Bot)
#
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

import html
import re

import anilist
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bs4 import BeautifulSoup
from jikanpy import AioJikan

from hitsuki.decorator import register

from .utils.disable import disableable_dec
from .utils.http import http
from .utils.language import get_strings_dec
from .utils.message import get_args_str, need_args_dec


def t(milliseconds: int) -> str:
    """
    Inputs time in milliseconds, to get beautified time, as string.

    Arguments:
        `milliseconds`: time in milliseconds.
    """
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = (
        ((str(days) + " Days, ") if days else "")
        + ((str(hours) + " Hours, ") if hours else "")
        + ((str(minutes) + " Minutes, ") if minutes else "")
        + ((str(seconds) + " Seconds, ") if seconds else "")
        + ((str(milliseconds) + " ms, ") if milliseconds else "")
    )
    return tmp[:-2]


@register(cmds="anime")
@need_args_dec()
@disableable_dec("anime")
@get_strings_dec("anime")
async def anilist_anime(message, strings):
    query = get_args_str(message)

    if query.isdecimal():
        anime_id = int(query)
    else:
        try:
            async with anilist.AsyncClient() as client:
                results = await client.search(query, "anime", 1)
                anime_id = results[0].id
        except IndexError:
            return await message.reply(strings["search_err"])

    async with anilist.AsyncClient() as client:
        anime = await client.get(anime_id)

    if not anime:
        return await message.reply(
            strings["search_get_err"].format(type="anime", id=anime_id)
        )

    if hasattr(anime, "description"):
        if len(anime.description) > 700:
            desc = strings["short_desc"].format(desc=anime.description_short)
        else:
            desc = strings["desc"].format(desc=anime.description)

    text = f"<b>{anime.title.romaji}</b> (<code>{anime.title.native}</code>)"
    text += strings["id"].format(id=anime.id)
    text += strings["anime_type"].format(type=anime.format)
    if hasattr(anime, "status"):
        text += strings["status"].format(status=anime.status)
    if hasattr(anime, "episodes"):
        text += strings["anime_episodes"].format(ep=anime.episodes)
    if hasattr(anime, "duration"):
        text += strings["anime_duration"].format(time=anime.duration)
    if hasattr(anime.score, "average"):
        text += strings["score"].format(score=anime.score.average)
    if hasattr(anime, "genres"):
        text += strings["genres"].format(
            genres=f" <code>{', '.join(str(x) for x in anime.genres)}</code>\n"
        )
    if hasattr(anime, "studios"):
        text += strings["anime_studios"].format(
            studios=f" <code>{', '.join(str(x) for x in anime.studios)}</code>\n"
        )
    if hasattr(anime, "description"):
        text += f"\n{desc.replace('<br>', '')}"

    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton(text=strings["more_info"], url=anime.url)
    )

    try:
        keyboard.insert(
            InlineKeyboardButton(text=strings["trailer"] + " 🎬", url=anime.trailer.url)
        )
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
@get_strings_dec("anime")
async def anilist_airing(message, strings):
    query = get_args_str(message)

    if query.isdecimal():
        anime_id = int(query)
    else:
        try:
            async with anilist.AsyncClient() as client:
                results = await client.search(query, "anime", 1)
                anime_id = results[0].id
        except IndexError:
            return await message.reply(strings["search_err"])

    async with anilist.AsyncClient() as client:
        anime = await client.get(anime_id)

    if not anime:
        return await message.reply(
            strings["search_get_err"].format(type="anime", id=anime_id)
        )

    text = f"<b>{anime.title.romaji}</b> (<code>{anime.title.native}</code>)"
    text += strings["id"].format(id=anime.id)
    text += strings["anime_type"].format(type=anime.format)
    if hasattr(anime, "next_airing"):
        airing_time = anime.next_airing.time_until * 1000
        text += strings["airing_episode"].format(ep=anime.next_airing.episode)
        text += strings["airing_time"].format(time=t(airing_time))
    else:
        text += strings["airing_episode"].format(ep=anime.episodes)
        text += strings["airing_time"].format(time="<code>N/A</code>")

    if hasattr(anime, "banner"):
        await message.reply_photo(photo=anime.banner, caption=text)
    else:
        await message.reply(text)


@register(cmds="manga")
@need_args_dec()
@disableable_dec("manga")
@get_strings_dec("anime")
async def anilist_manga(message, strings):
    query = get_args_str(message)

    if query.isdecimal():
        manga_id = int(query)
    else:
        try:
            async with anilist.AsyncClient() as client:
                results = await client.search(query, "manga", 1)
                manga_id = results[0].id
        except IndexError:
            return await message.reply(strings["search_err"])

    async with anilist.AsyncClient() as client:
        manga = await client.get(manga_id, "manga")

    if not manga:
        return await message.reply(
            strings["search_get_err"].format(type="manga", id=manga_id)
        )

    if hasattr(manga, "description"):
        if len(manga.description) > 700:
            desc = strings["short_desc"].format(desc=manga.description_short)
        else:
            desc = strings["desc"].format(desc=manga.description)

    text = f"<b>{manga.title.romaji}</b> (<code>{manga.title.native}</code>)"
    text += strings["id"].format(id=manga.id)
    if hasattr(manga.start_date, "year"):
        text += strings["manga_start"].format(date=manga.start_date.year)
    if hasattr(manga, "status"):
        text += strings["status"].format(status=manga.status)
    if hasattr(manga, "chapters"):
        text += strings["manga_chapters"].format(chapters=manga.chapters)
    if hasattr(manga, "volumes"):
        text += strings["manga_volumes"].format(vol=manga.volumes)
    if hasattr(manga.score, "average"):
        text += strings["score"].format(score=manga.score.average)
    if hasattr(manga, "genres"):
        text += strings["genres"].format(
            genres=f" <code>{', '.join(str(x) for x in manga.genres)}</code>\n"
        )
    if hasattr(manga, "description"):
        text += f"\n{desc.replace('<br>', '')}"

    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton(text=strings["more_info"], url=manga.url)
    )

    await message.reply_photo(
        photo=f"https://img.anili.st/media/{manga.id}",
        caption=text,
        reply_markup=keyboard,
    )


@register(cmds="character")
@need_args_dec()
@disableable_dec("character")
@get_strings_dec("anime")
async def anilist_character(message, strings):
    query = get_args_str(message)

    if query.isdecimal():
        character_id = int(query)
    else:
        try:
            async with anilist.AsyncClient() as client:
                results = await client.search(query, "char", 1)
                character_id = results[0].id
        except IndexError:
            return await message.reply(strings["search_err"])

    async with anilist.AsyncClient() as client:
        character = await client.get(character_id, "char")

    if not character:
        return await message.reply(
            strings["search_get_err"].format(type="character", id=character_id)
        )

    if hasattr(character, "description"):
        desc = character.description
        desc = desc.replace("__", "")
        desc = desc.replace("**", "")
        desc = desc.replace("~", "")
        desc = re.sub(re.compile(r"<.*?>"), "", desc)
        if len(character.description) > 700:
            desc = desc[0:500] + "[...]"
            desc = strings["char_desc"].format(desc=desc)
        else:
            desc = strings["char_desc"].format(desc=desc)

    text = f"<b>{character.name.full}</b> (<code>{character.name.native}</code>)"
    text += strings["id"].format(id=character.id)
    if hasattr(character, "favorites"):
        text += strings["favorites"].format(favs=character.favorites)
    if hasattr(character, "description"):
        text += f"\n\n{desc}"

    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton(text=strings["more_info"], url=character.url)
    )

    if hasattr(character, "image"):
        await message.reply_photo(
            photo=character.image.large,
            caption=text,
            reply_markup=keyboard,
        )
    else:
        await message.reply(text, reply_markup=keyboard)


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


async def site_search(message, strings, site: str):
    search_query = get_args_str(message)
    more_results = True

    if site == "kaizoku":
        search_url = f"https://animekaizoku.com/?s={search_query}"
        html_text = await http.get(search_url)
        if html_text.status_code in (500, 521):
            await message.reply(strings["unknown_search_err"])
            return

        soup = BeautifulSoup(html_text.text, "lxml")
        search_result = soup.find_all("h2", {"class": "post-title"})

        if search_result:
            result = strings["search_kaizoku"].format(query=html.escape(search_query))
            for entry in search_result:
                post_link = entry.a["href"]
                post_name = html.escape(entry.text)
                result += f"• <a href='{post_link}'>{post_name}</a>\n"
        else:
            more_results = False
            result = strings["kaizoku_err"].format(query=html.escape(search_query))

    elif site == "kayo":
        search_url = f"https://animekayo.com/?s={search_query}"
        html_text = await http.get(search_url)
        if html_text.status_code in (500, 521):
            await message.reply(strings["unknown_search_err"])
            return

        soup = BeautifulSoup(html_text.text, "lxml")
        search_result = soup.find_all("h2", {"class": "title"})

        result = strings["search_kayo"].format(query=html.escape(search_query))
        for entry in search_result:

            if entry.text.strip() == "Nothing Found":
                result = strings["kayo_err"].format(query=html.escape(search_query))
                more_results = False
                break

            post_link = entry.a["href"]
            post_name = html.escape(entry.text.strip())
            result += f"• <a href='{post_link}'>{post_name}</a>\n"

    buttons = InlineKeyboardMarkup().add(
        InlineKeyboardButton(text=strings["all_results"], url=search_url)
    )

    if more_results:
        await message.reply(result, reply_markup=buttons, disable_web_page_preview=True)
    else:
        await message.reply(result, disable_web_page_preview=True)


@register(cmds="kaizoku")
@need_args_dec()
@disableable_dec("kaizoku")
@get_strings_dec("anime")
async def kaizoku(message, strings):
    await site_search(message, strings, "kaizoku")


@register(cmds="kayo")
@need_args_dec()
@disableable_dec("kayo")
@get_strings_dec("anime")
async def kayo(message, strings):
    await site_search(message, strings, "kayo")


__mod_name__ = "Anime"

__help__ = """
Get information about anime, manga or anime characters.

<b>Available commands:</b>
- /anime (anime): returns information about the anime.
- /manga (manga): returns information about the manga.
- /airing (anime): returns anime airing info.
- /character (character): returns information about the character.
- /kaizoku (anime): search an anime on animekaizoku.com
- /kayo (anime): search an anime on animekayo.com
- /upcoming: returns a list of new anime in the upcoming seasons.
"""
