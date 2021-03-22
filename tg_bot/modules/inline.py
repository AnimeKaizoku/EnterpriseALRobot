from datetime import datetime
import html
import re
import time
import json
from html.parser import HTMLParser
from platform import python_version
from uuid import uuid4
import requests, json
from spamprotection.errors import HostDownError
from spamprotection.sync import SPBClient
from telegram import InlineQueryResultArticle, ParseMode, InputTextMessageContent, Update, InlineKeyboardMarkup, \
    InlineKeyboardButton
from telegram import __version__
from telegram.error import BadRequest
from telegram.ext import InlineQueryHandler, CallbackContext
from telegram.utils.helpers import mention_html
from tg_bot.modules.helper_funcs.misc import article
import tg_bot.modules.sql.users_sql as sql
from tg_bot import (
    dispatcher,
    OWNER_ID,
    SUDO_USERS,
    SUPPORT_USERS,
    DEV_USERS,
    SARDEGNA_USERS,
    WHITELIST_USERS,
    sw, log
)

client = SPBClient()


def remove_prefix(text, prefix):
    if text.startswith(prefix):
        text = text.replace(prefix, "", 1)
    return text

def inlinequery(update: Update, _) -> None:
    """
    Main InlineQueryHandler callback.
    """
    query = update.inline_query.query
    user = update.effective_user

    results: List = []
    inline_help_dicts = [
        {
            "title": "SpamProtection INFO",
            "description": "Look up a person on @Intellivoid SpamProtection API",
            "message_text":"Click the button below to look up a person on @Intellivoid SpamProtection API using username or telegram id",
            "thumb_urL": "https://telegra.ph/file/3ce9045b1c7faf7123c67.jpg",
            "keyboard": ".spb ",
        },
        {
            "title": "User info on Kigyo",
            "description": "Look up a person in Kigyo database",
            "message_text": "Click the button below to look up a person in Kigyo database using their Telegram ID",
            "thumb_urL": "https://telegra.ph/file/c85e07b58f5b3158b529a.jpg",
            "keyboard": ".info ",
        },
        {
            "title": "About",
            "description": "Know about Kigyo",
            "message_text": "Click the button below to get to know about Kigyo.",
            "thumb_urL": "https://telegra.ph/file/c85e07b58f5b3158b529a.jpg",
            "keyboard": ".about ",
        },
        {
            "title": "Anilist",
            "description": "Search anime and manga on AniList.co",
            "message_text": "Click the button below to search anime and manga on AniList.co",
            "thumb_urL": "https://telegra.ph/file/c85e07b58f5b3158b529a.jpg",
            "keyboard": ".anilist ",
        },
    ]

    inline_funcs = {
        ".spb": spb,
        ".info": inlineinfo,
        ".about": about,
        ".anilist": media_query,
    }

    if (f := query.split(" ", 1)[0]) in inline_funcs:
        inline_funcs[f](remove_prefix(query, f).strip(), update, user)
    else:
        for ihelp in inline_help_dicts:
            results.append(
                article(
                    title=ihelp["title"],
                    description=ihelp["description"],
                    message_text=ihelp["message_text"],
                    thumb_url=ihelp["thumb_urL"],
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    text="Click Here",
                                    switch_inline_query_current_chat=ihelp[
                                        "keyboard"
                                    ],
                                )
                            ]
                        ]
                    ),
                )
            )

        update.inline_query.answer(results, cache_time=5)

def inlineinfo(query: str, update: Update, context: CallbackContext) -> None:
    """Handle the inline query."""
    bot = context.bot
    query = update.inline_query.query
    log.info(query)
    user_id = update.effective_user.id

    try:
        search = query.split(" ", 1)[1]
    except IndexError:
        search = user_id

    try:
        user = bot.get_chat(int(search))
    except (BadRequest, ValueError):
        user = bot.get_chat(user_id)

    chat = update.effective_chat
    sql.update_user(user.id, user.username)

    text = (
        f"<b>General:</b>\n"
        f"ID: <code>{user.id}</code>\n"
        f"First Name: {html.escape(user.first_name)}"
    )

    if user.last_name:
        text += f"\nLast Name: {html.escape(user.last_name)}"

    if user.username:
        text += f"\nUsername: @{html.escape(user.username)}"

    text += f"\nPermanent user link: {mention_html(user.id, 'link')}"

    try:
        spamwtc = sw.get_ban(int(user.id))
        if spamwtc:
            text += "<b>\n\nSpamWatch:\n</b>"
            text += "<b>This person is banned in Spamwatch!</b>"
            text += f"\nReason: <pre>{spamwtc.reason}</pre>"
            text += "\nAppeal at @SpamWatchSupport"
        else:
            text += "<b>\n\nSpamWatch:</b>\n Not banned"
    except:
        pass  # don't crash if api is down somehow...

    try:
        status = client.raw_output(int(user.id))
        ptid = status["results"]["private_telegram_id"]
        op = status["results"]["attributes"]["is_operator"]
        ag = status["results"]["attributes"]["is_agent"]
        wl = status["results"]["attributes"]["is_whitelisted"]
        ps = status["results"]["attributes"]["is_potential_spammer"]
        sp = status["results"]["spam_prediction"]["spam_prediction"]
        hamp = status["results"]["spam_prediction"]["ham_prediction"]
        blc = status["results"]["attributes"]["is_blacklisted"]
        if blc:
            blres = status["results"]["attributes"]["blacklist_reason"]
        else:
            blres = None
        text += "\n\n<b>SpamProtection:</b>"
        text += f"<b>\nPrivate Telegram ID:</b> <code>{ptid}</code>\n"
        text += f"<b>Operator:</b> <code>{op}</code>\n"
        text += f"<b>Agent:</b> <code>{ag}</code>\n"
        text += f"<b>Whitelisted:</b> <code>{wl}</code>\n"
        text += f"<b>Spam Prediction:</b> <code>{sp}</code>\n"
        text += f"<b>Ham Prediction:</b> <code>{hamp}</code>\n"
        text += f"<b>Potential Spammer:</b> <code>{ps}</code>\n"
        text += f"<b>Blacklisted:</b> <code>{blc}</code>\n"
        text += f"<b>Blacklist Reason:</b> <code>{blres}</code>\n"
    except HostDownError:
        text += "\n\n<b>SpamProtection:</b>"
        text += "\nCan't connect to Intellivoid SpamProtection API\n"

    nation_level_present = False

    num_chats = sql.get_user_num_chats(user.id)
    text += f"\nChat count: <code>{num_chats}</code>"

    if user.id == OWNER_ID:
        text += f"\nThis person is my owner"
        nation_level_present = True
    elif user.id in DEV_USERS:
        text += f"\nThis Person is a part of Eagle Union"
        nation_level_present = True
    elif user.id in SUDO_USERS:
        text += f"\nThe Nation level of this person is Royal"
        nation_level_present = True
    elif user.id in SUPPORT_USERS:
        text += f"\nThe Nation level of this person is Sakura"
        nation_level_present = True
    elif user.id in SARDEGNA_USERS:
        text += f"\nThe Nation level of this person is Sardegna"
        nation_level_present = True
    elif user.id in WHITELIST_USERS:
        text += f"\nThe Nation level of this person is Neptunia"
        nation_level_present = True

    if nation_level_present:
        text += ' [<a href="https://t.me/{}?start=nations">?</a>]'.format(bot.username)

    results = [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title=f"User info of {html.escape(user.first_name)}",
            input_message_content=InputTextMessageContent(text, parse_mode=ParseMode.HTML,
                                                          disable_web_page_preview=True),
        ),
    ]

    update.inline_query.answer(results, cache_time=5)


def about(query: str, update: Update, context: CallbackContext) -> None:
    """Handle the inline query."""
    query = update.inline_query.query
    user_id = update.effective_user.id
    user = context.bot.get_chat(user_id)
    sql.update_user(user.id, user.username)
    about_text = f"""
    Kigyo (@{context.bot.username})
    Maintained by [Dank-del](t.me/dank_as_fuck)
    Built with ❤️ using python-telegram-bot v{str(__version__)}
    Running on Python {python_version()}
    """
    results: list = []
    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="Support",
                    url=f"https://t.me/YorktownEagleUnion",
                ),
                InlineKeyboardButton(
                    text="Channel",
                    url=f"https://t.me/KigyoUpdates",
                ),

            ],
            [
                InlineKeyboardButton(
                    text="GitLab",
                    url=f"https://www.gitlab.com/Dank-del/EnterpriseALRobot",
                ),
                InlineKeyboardButton(
                    text="GitHub",
                    url="https://www.github.com/Dank-del/EnterpriseALRobot",
                ),
            ],
        ])

    results.append(

        InlineQueryResultArticle
            (
            id=str(uuid4()),
            title=f"About Kigyo (@{context.bot.username})",
            input_message_content=InputTextMessageContent(about_text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True),
            reply_markup=kb
            )
       )
    update.inline_query.answer(results)

def spb(query: str, update: Update, context: CallbackContext) -> None:
    """Handle the inline query."""
    query = update.inline_query.query
    user_id = update.effective_user.id

    try:
        search = query.split(" ", 1)[1]
    except IndexError:
        search = user_id

    if search:
        srdata = search
    else:
        srdata = user_id

    url = f"https://api.intellivoid.net/spamprotection/v1/lookup?query={srdata}"
    r = requests.get(url)
    a = r.json()
    response = a["success"]
    if response is True:
        date = a["results"]["last_updated"]
        stats = f"*◢ Intellivoid• SpamProtection Info*:\n"
        stats += f' • *Updated on*: `{datetime.fromtimestamp(date).strftime("%Y-%m-%d %I:%M:%S %p")}`\n'

        if a["results"]["attributes"]["is_potential_spammer"] is True:
            stats += f" • *User*: `USERxSPAM`\n"
        elif a["results"]["attributes"]["is_operator"] is True:
            stats += f" • *User*: `USERxOPERATOR`\n"
        elif a["results"]["attributes"]["is_agent"] is True:
            stats += f" • *User*: `USERxAGENT`\n"
        elif a["results"]["attributes"]["is_whitelisted"] is True:
            stats += f" • *User*: `USERxWHITELISTED`\n"

        stats += f' • *Type*: `{a["results"]["entity_type"]}`\n'
        stats += (
            f' • *Language*: `{a["results"]["language_prediction"]["language"]}`\n'
        )
        stats += f' • *Language Probability*: `{a["results"]["language_prediction"]["probability"]}`\n'
        stats += f"*Spam Prediction*:\n"
        stats += f' • *Ham Prediction*: `{a["results"]["spam_prediction"]["ham_prediction"]}`\n'
        stats += f' • *Spam Prediction*: `{a["results"]["spam_prediction"]["spam_prediction"]}`\n'
        stats += f'*Blacklisted*: `{a["results"]["attributes"]["is_blacklisted"]}`\n'
        if a["results"]["attributes"]["is_blacklisted"] is True:
            stats += (
                f' • *Reason*: `{a["results"]["attributes"]["blacklist_reason"]}`\n'
            )
            stats += f' • *Flag*: `{a["results"]["attributes"]["blacklist_flag"]}`\n'
        stats += f'*PTID*:\n`{a["results"]["private_telegram_id"]}`\n'

    else:
        stats = "`cannot reach SpamProtection API`"

    results = [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title=f"SpamProtection API info of {srdata}",
            input_message_content=InputTextMessageContent(stats, parse_mode=ParseMode.MARKDOWN,
                                                          disable_web_page_preview=True),
        ),
    ]

    update.inline_query.answer(results, cache_time=5)


# Anilist stuff begins // queries written by github.com/the-blank-x (t.me/TheKneesocks) // parser by github.com/Dank-del (t.me/dank_as_fuck)

MEDIA_QUERY = '''query ($search: String) {
  Page (perPage: 10) {
    media (search: $search) {
      id
      title {
        romaji
        english
        native
      }
      type
      format
      status
      description
      episodes
      duration
      chapters
      volumes
      genres
      synonyms
      averageScore
      airingSchedule(notYetAired: true) {
        nodes {
          airingAt
          timeUntilAiring
          episode
        }
      }
      siteUrl
    }
  }
}'''


def media_query(query: str, update: Update, context: CallbackContext) -> None:
    """
    Handle anime inline query.
    """
    results: List = []

    try:
        search = query.split(" ", 1)[1]
        results: List = []
        r = requests.post('https://graphql.anilist.co', data=json.dumps({'query': MEDIA_QUERY, 'variables': {'search': search}}), headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
        res = r.json()
        data = res['data']['Page']['media']
        res = data
        for data in res:
            title_en = data["title"].get("english") or "N/A"
            title_ja = data["title"].get("romaji") or "N/A"
            format = data.get("format") or "N/A"
            type = data.get("type") or "N/A"
            try:
                des = data.get("description").replace("<br>", "").replace("</br>", "")
                description = des.replace("<i>", "").replace("</i>", "") or "N/A"
            except AttributeError:
                description = data.get("description")

            avgsc = data.get("averageScore") or "N/A"
            status = data.get("status") or "N/A"
            genres = data.get("genres") or "N/A"
            genres = ", ".join(genres)
            img = f"https://img.anili.st/media/{data['id']}" or ""
            aurl = data.get("siteUrl")
            kb = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Read More",
                            url=aurl,
                        )
                        ]

                    ])

            txt = f"{title_en} | {title_ja}\n"
            txt += f"Format: {format}\n"
            txt += f"Type: {type}\n"
            txt += f"Average Score: {avgsc}\n"
            txt += f"Status: {status}\n"
            txt += f"Genres: {genres}\n"
            txt += f"Description: {description}\n"
            txt += f"<a href='{img}'>&#xad</a>"

            results.append(
                InlineQueryResultArticle
                    (
                    id=str(uuid4()),
                    title=f"{title_en} | {title_ja}",
                    thumb_url=img,
                    description=f"{description}",
                    input_message_content=InputTextMessageContent(txt, parse_mode=ParseMode.HTML, disable_web_page_preview=False)
                    )
        )
    except (IndexError):
        results.append(

            InlineQueryResultArticle
                (
                id=str(uuid4()),
                title=f"Media {query} not found",
                input_message_content=InputTextMessageContent(f"Media {query} not found", reply_markup=kb, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
                )
           )

    update.inline_query.answer(results, cache_time=5)





dispatcher.add_handler(InlineQueryHandler(inlinequery))
