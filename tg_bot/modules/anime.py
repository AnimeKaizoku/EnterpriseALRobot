# Module to get info about anime, characters, manga etc. by @TheRealPhoenix

from jikanpy import Jikan
import requests
import json
from jikanpy.exceptions import APIException

from telegram import ParseMode, Update, Bot, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler,  run_async

from tg_bot import dispatcher

jikan = Jikan()

kaizoku_btn = "Kaizoku ☠️"
kayo_btn = "Kayo 🏴‍☠️"
close_btn = "Close ❌"


def anime_call_api(search_str):
    query = '''
    query ($id: Int,$search: String) { 
      Media (id: $id, type: ANIME,search: $search) { 
        id
        title {
          romaji
          english
        }
        description (asHtml: false)
        startDate{
            year
          }
          episodes
          chapters
          volumes
          season
          type
          format
          status
          duration
          averageScore
          genres
          bannerImage
      }
    }
    '''
    variables = {
        'search' : search_str
    }
    url = 'https://graphql.anilist.co'
    response = requests.post(url, json={'query': query, 'variables': variables})
    return response.text


def formatJSON(outData):
    msg = ""
    jsonData = json.loads(outData)
    res = list(jsonData.keys())
    if "errors" in res:
        msg += f"**Error** : `{jsonData['errors'][0]['message']}`"
        return msg
    else:
        jsonData = jsonData['data']['Media']
        if "bannerImage" in jsonData.keys():
            msg += f"[💮]({jsonData['bannerImage']})"
        else:
            msg += "💮"
        title = jsonData['title']['romaji']
        link = f"https://anilist.co/anime/{jsonData['id']}"
        msg += f"[{title}]({link})"
        msg += f"\n\n**Type** : {jsonData['format']}"
        msg += f"\n**Genres** : "
        for g in jsonData['genres']:
            msg += g+" "
        msg += f"\n**Status** : {jsonData['status']}"
        msg += f"\n**Episode** : {jsonData['episodes']}"
        msg += f"\n**Year** : {jsonData['startDate']['year']}"
        msg += f"\n**Score** : {jsonData['averageScore']}"
        msg += f"\n**Duration** : {jsonData['duration']} min"
        msg += f"\n\n __{jsonData['description']}__"
        return msg


@run_async
def anime(_bot: Bot, update: Update, args):
    message = update.effective_message
    query = " ".join(args)
    result = anime_call_api(query)
    msg = formatJSON(result)
    yt_search = query.replace(" ", "+")
    url_link = f"https://www.youtube.com/results?search_query={yt_search}"
    kaizoku = f'https://animekaizoku.com/?s={query}'
    kayo = f'https://animekayo.com/?s={query}'
    buttons = [[InlineKeyboardButton("🎥Trailer", url=url_link)],
               [InlineKeyboardButton(kaizoku_btn, url=kaizoku), InlineKeyboardButton(kayo_btn, url=kayo)]]
    message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(buttons))
    

@run_async
def character(_bot: Bot, update: Update, args):
    msg = update.effective_message
    res = ""
    query = " ".join(args)
    try:
        search = jikan.search("character", query).get("results")[0].get("mal_id")
    except APIException:
        msg.reply_text("No results found!")
        return ""
    if search:
        try:
            res = jikan.character(search)
        except APIException:
            msg.reply_text("Error connecting to the API. Please try again!")
            return ""
    if res:
        name = res.get("name")
        kanji = res.get("name_kanji")
        about = res.get("about")
        if len(about) > 4096:
            about = about[:4000] + "..."
        image = res.get("image_url")
        url = res.get("url")
        rep = f"<b>{name} ({kanji})</b>\n\n"
        rep += f"<a href='{image}'>\u200c</a>"
        rep += f"<i>{about}</i>\n"
        keyb = [
            [InlineKeyboardButton("More Information", url=url)]
        ]
        
        msg.reply_text(rep, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyb))
        
        
@run_async
def upcoming(_bot: Bot, update: Update):
    msg = update.effective_message
    rep = "<b>Upcoming anime</b>\n"
    later = jikan.season_later()
    anime = later.get("anime")
    for new in anime:
        name = new.get("title")
        url = new.get("url")
        rep += f"• <a href='{url}'>{name}</a>\n"
        if len(rep) > 2000:
            break
    msg.reply_text(rep, parse_mode=ParseMode.HTML)
    
    
@run_async
def manga(_bot: Bot, update: Update, args):
    msg = update.effective_message
    query = " ".join(args)
    try:
        res = jikan.search("manga", query).get("results")[0].get("mal_id")
    except APIException:
        msg.reply_text("Error connecting to the API. Please try again!")
        return ""
    if res:
        try:
            manga = jikan.manga(res)
        except APIException:
            msg.reply_text("Error connecting to the API. Please try again!")
            return ""
        title = manga.get("title")
        japanese = manga.get("title_japanese")
        type = manga.get("type")
        status = manga.get("status")
        score = manga.get("score")
        volumes = manga.get("volumes")
        chapters = manga.get("chapters")
        genre_lst = manga.get("genres")
        genres = ""
        for genre in genre_lst:
            genres += genre.get("name") + ", "
        genres = genres[:-2]
        synopsis = manga.get("synopsis")
        image = manga.get("image_url")
        url = manga.get("url")
        rep = f"<b>{title} ({japanese})</b>\n"
        rep += f"<b>Type:</b> <code>{type}</code>\n"
        rep += f"<b>Status:</b> <code>{status}</code>\n"
        rep += f"<b>Genres:</b> <code>{genres}</code>\n"
        rep += f"<b>Score:</b> <code>{score}</code>\n"
        rep += f"<b>Volumes:</b> <code>{volumes}</code>\n"
        rep += f"<b>Chapters:</b> <code>{chapters}</code>\n\n"
        rep += f"<a href='{image}'>\u200c</a>"
        rep += f"<i>{synopsis}</i>"
        keyb = [
            [InlineKeyboardButton("More Information", url=url)]
        ]
        
        msg.reply_text(rep, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyb))
        
        
__help__ = """
Get information about anime, manga or characters with the help of this module! All data is fetched from [MyAnimeList](https://myanimelist.net).

*Available commands:*
 - /sanime <anime>: returns information about the anime.
 - /scharacter <character>: returns information about the character.
 - /smanga <manga>: returns information about the manga.
 - /upcoming: returns a list of new anime in the upcoming seasons.
 """

__mod_name__ = "MyAnimeList"
        
        
ANIME_HANDLER = CommandHandler("anime", anime, pass_args=True)
CHARACTER_HANDLER = CommandHandler("character", character, pass_args=True)
UPCOMING_HANDLER = CommandHandler("upcoming", upcoming)
MANGA_HANDLER = CommandHandler("manga", manga, pass_args=True)

dispatcher.add_handler(ANIME_HANDLER)
dispatcher.add_handler(CHARACTER_HANDLER)
dispatcher.add_handler(UPCOMING_HANDLER)
dispatcher.add_handler(MANGA_HANDLER)