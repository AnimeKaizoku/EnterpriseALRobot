# Module to get info about anime, characters, manga etc. by @TheRealPhoenix

from jikanpy import Jikan
from jikanpy.exceptions import APIException

from telegram import Message, Chat, User, ParseMode, Update, Bot, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler,  run_async

from tg_bot import dispatcher

jikan = Jikan()


@run_async
def anime(bot: Bot, update: Update, args):
    msg = update.effective_message
    query = " ".join(args)
    res = ""
    try:
        res = jikan.search("anime", query)
    except APIException:
        msg.reply_text("Error connecting to the API. Please try again!")
        return ""
    try:
        res = res.get("results")[0].get("mal_id") # Grab first result
    except APIException:
        msg.reply_text("Error connecting to the API. Please try again!")
        return ""
    if res:
        anime = jikan.anime(res)
        title = anime.get("title")
        japanese = anime.get("title_japanese")
        type = anime.get("type")
        duration = anime.get("duration")
        synopsis = anime.get("synopsis")
        source = anime.get("source")
        status = anime.get("status")
        episodes = anime.get("episodes")
        score = anime.get("score")
        rating = anime.get("rating")
        genre_lst = anime.get("genres")
        genres = ""
        for genre in genre_lst:
            genres += genre.get("name") + ", "
        genres = genres[:-2]
        studios = ""
        studio_lst = anime.get("studios")
        for studio in studio_lst:
            studios += studio.get("name") + ", "
        studios = studios[:-2]
        duration = anime.get("duration")
        premiered = anime.get("premiered")
        image_url = anime.get("image_url")
        url = anime.get("url")
        trailer = anime.get("trailer_url")
    else:
        msg.reply_text("No results found!")
        return
    rep = f"<b>{title} ({japanese})</b>\n"
    rep += f"<b>Type:</b> <code>{type}</code>\n"
    rep += f"<b>Source:</b> <code>{source}</code>\n"
    rep += f"<b>Status:</b> <code>{status}</code>\n"
    rep += f"<b>Genres:</b> <code>{genres}</code>\n"
    rep += f"<b>Episodes:</b> <code>{episodes}</code>\n"
    rep += f"<b>Duration:</b> <code>{duration}</code>\n"
    rep += f"<b>Score:</b> <code>{score}</code>\n"
    rep += f"<b>Studio(s):</b> <code>{studios}</code>\n"
    rep += f"<b>Premiered:</b> <code>{premiered}</code>\n"
    rep += f"<b>Rating:</b> <code>{rating}</code>\n\n"
    rep += f"<a href='{image_url}'>\u200c</a>"
    rep += f"<i>{synopsis}</i>\n"
    if trailer:
        keyb = [
            [InlineKeyboardButton("More Information", url=url),
           InlineKeyboardButton("Trailer", url=trailer)]
        ]
    else:
        keyb = [
             [InlineKeyboardButton("More Information", url=url)]
         ]
    
    
    msg.reply_text(rep, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyb))
    

@run_async
def character(bot: Bot, update: Update, args):
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
def upcoming(bot: Bot, update: Update):
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
def manga(bot: Bot, update: Update, args):
    msg = update.effective_message
    query = " ".join(args)
    res = ""
    manga = ""
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
        
        
ANIME_HANDLER = CommandHandler("sanime", anime, pass_args=True)
CHARACTER_HANDLER = CommandHandler("scharacter", character, pass_args=True)
UPCOMING_HANDLER = CommandHandler("upcoming", upcoming)
MANGA_HANDLER = CommandHandler("smanga", manga, pass_args=True)

dispatcher.add_handler(ANIME_HANDLER)
dispatcher.add_handler(CHARACTER_HANDLER)
dispatcher.add_handler(UPCOMING_HANDLER)
dispatcher.add_handler(MANGA_HANDLER)
