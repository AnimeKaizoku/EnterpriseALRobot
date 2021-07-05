import html
import json
from datetime import datetime
from platform import python_version
from typing import List
from uuid import uuid4

import requests
from telegram import InlineQueryResultArticle, ParseMode, InputTextMessageContent, Update, InlineKeyboardMarkup, \
    InlineKeyboardButton
from telegram import __version__
from telegram.error import BadRequest
from telegram.ext import CallbackContext
from telegram.utils.helpers import mention_html

import tg_bot.modules.sql.users_sql as sql
from tg_bot import (
    OWNER_ID,
    SUDO_USERS,
    SUPPORT_USERS,
    DEV_USERS,
    SARDEGNA_USERS,
    WHITELIST_USERS,
    sw, log
)
from tg_bot.modules.helper_funcs.misc import article
from tg_bot.modules.helper_funcs.decorators import kiginline


def remove_prefix(text, prefix):
    if text.startswith(prefix):
        text = text.replace(prefix, "", 1)
    return text

@kiginline()
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
            "description": "Look up a person/bot/channel/chat on @Intellivoid SpamProtection API",
            "message_text": "Click the button below to look up a person/bot/channel/chat on @Intellivoid SpamProtection API using "
                            "username or telegram id",
            "thumb_urL": "https://telegra.ph/file/3ce9045b1c7faf7123c67.jpg",
            "keyboard": ".spb ",
        },
        {
            "title": "Account info on Kigyo",
            "description": "Look up a Telegram account in Kigyo database",
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
            "title": "Anime",
            "description": "Search anime and manga on AniList.co",
            "message_text": "Click the button below to search anime and manga on AniList.co",
            "thumb_urL": "https://telegra.ph/file/c85e07b58f5b3158b529a.jpg",
            "keyboard": ".anime ",
        },
        {
            "title": "Character",
            "description": "Search Characters on AniList.co",
            "message_text": "Search character on AniList.co",
            "thumb_urL": "https://telegra.ph/file/a546976e6f3ebf21a131a.jpg",
            "keyboard": ".char ",
        },
    ]

    inline_funcs = {
        ".spb": spb,
        ".info": inlineinfo,
        ".about": about,
        ".anime": media_query,
        ".char": character_query,
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
        f"<b>Information:</b>\n"
        f"• ID: <code>{user.id}</code>\n"
        f"• First Name: {html.escape(user.first_name)}"
    )

    if user.last_name:
        text += f"\n• Last Name: {html.escape(user.last_name)}"

    if user.username:
        text += f"\n• Username: @{html.escape(user.username)}"

    text += f"\n• Permanent user link: {mention_html(user.id, 'link')}"

    nation_level_present = False

    if user.id == OWNER_ID:
        text += f"\n\nThis person is my owner"
        nation_level_present = True
    elif user.id in DEV_USERS:
        text += f"\n\nThis Person is a part of Eagle Union"
        nation_level_present = True
    elif user.id in SUDO_USERS:
        text += f"\n\nThe Nation level of this person is Royal"
        nation_level_present = True
    elif user.id in SUPPORT_USERS:
        text += f"\n\nThe Nation level of this person is Sakura"
        nation_level_present = True
    elif user.id in SARDEGNA_USERS:
        text += f"\n\nThe Nation level of this person is Sardegna"
        nation_level_present = True
    elif user.id in WHITELIST_USERS:
        text += f"\n\nThe Nation level of this person is Neptunia"
        nation_level_present = True

    if nation_level_present:
        text += ' [<a href="https://t.me/{}?start=nations">?</a>]'.format(bot.username)

    try:
        spamwtc = sw.get_ban(int(user.id))
        if spamwtc:
            text += "<b>\n\n• SpamWatched:\n</b> Yes"
            text += f"\n• Reason: <pre>{spamwtc.reason}</pre>"
            text += "\n• Appeal at @SpamWatchSupport"
        else:
            text += "<b>\n\n• SpamWatched:</b> No"
    except:
        pass  # don't crash if api is down somehow...

    num_chats = sql.get_user_num_chats(user.id)
    text += f"\n• <b>Chat count</b>: <code>{num_chats}</code>"




    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="Report Error",
                    url=f"https://t.me/YorktownEagleUnion",
                ),
                InlineKeyboardButton(
                    text="Search again",
                    switch_inline_query_current_chat=".info ",
                ),

            ],
        ]
        )

    results = [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title=f"User info of {html.escape(user.first_name)}",
            input_message_content=InputTextMessageContent(text, parse_mode=ParseMode.HTML,
                                                          disable_web_page_preview=True),
            reply_markup=kb
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
                InlineKeyboardButton(
                    text='Ping',
                    callback_data='pingCB'
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
            input_message_content=InputTextMessageContent(about_text, parse_mode=ParseMode.MARKDOWN,
                                                          disable_web_page_preview=True),
            reply_markup=kb
        )
    )
    update.inline_query.answer(results)


def spb(query: str, update: Update, context: CallbackContext) -> None:
    """Handle the inline query."""
    query = update.inline_query.query
    user_id = update.effective_user.id
    srdata = None
    apst = requests.get(f'https://api.intellivoid.net/spamprotection/v1/lookup?query={context.bot.username}')
    api_status = apst.status_code
    if (api_status != 200):
        stats = f"API RETURNED {api_status}"
    else:
        try:
            search = query.split(" ", 1)[1]
        except IndexError:
            search = user_id

        srdata = search or user_id
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

    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="Report Error",
                    url=f"https://t.me/YorktownEagleUnion",
                ),
                InlineKeyboardButton(
                    text="Search again",
                    switch_inline_query_current_chat=".spb ",
                ),

            ],
        ])

    a = "the entity was not found"
    results = [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title=f"SpamProtection API info of {srdata or a}",
            input_message_content=InputTextMessageContent(stats, parse_mode=ParseMode.MARKDOWN,
                                                          disable_web_page_preview=True),
            reply_markup=kb
        ),
    ]

    update.inline_query.answer(results, cache_time=5)



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
      bannerImage
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
        results: List = []
        r = requests.post('https://graphql.anilist.co',
                          data=json.dumps({'query': MEDIA_QUERY, 'variables': {'search': query}}),
                          headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
        res = r.json()
        data = res['data']['Page']['media']
        res = data
        for data in res:
            title_en = data["title"].get("english") or "N/A"
            title_ja = data["title"].get("romaji") or "N/A"
            format = data.get("format") or "N/A"
            type = data.get("type") or "N/A"
            bannerimg = data.get("bannerImage") or "https://telegra.ph/file/cc83a0b7102ad1d7b1cb3.jpg"
            try:
                des = data.get("description").replace("<br>", "").replace("</br>", "")
                description = des.replace("<i>", "").replace("</i>", "") or "N/A"
            except AttributeError:
                description = data.get("description")

            try:
                description = html.escape(description)
            except AttributeError:
                description = description or "N/A"

            if len((str(description))) > 700:
                description = description [0:700] + "....."

            avgsc = data.get("averageScore") or "N/A"
            status = data.get("status") or "N/A"
            genres = data.get("genres") or "N/A"
            genres = ", ".join(genres)
            img = f"https://img.anili.st/media/{data['id']}" or "https://telegra.ph/file/cc83a0b7102ad1d7b1cb3.jpg"
            aurl = data.get("siteUrl")


            kb = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Read More",
                            url=aurl,
                        ),
                        InlineKeyboardButton(
                            text="Search again",
                            switch_inline_query_current_chat=".anime ",
                        ),

                    ],
                ])

            txt = f"<b>{title_en} | {title_ja}</b>\n"
            txt += f"<b>Format</b>: <code>{format}</code>\n"
            txt += f"<b>Type</b>: <code>{type}</code>\n"
            txt += f"<b>Average Score</b>: <code>{avgsc}</code>\n"
            txt += f"<b>Status</b>: <code>{status}</code>\n"
            txt += f"<b>Genres</b>: <code>{genres}</code>\n"
            txt += f"<b>Description</b>: <code>{description}</code>\n"
            txt += f"<a href='{img}'>&#xad</a>"

            results.append(
                InlineQueryResultArticle
                    (
                    id=str(uuid4()),
                    title=f"{title_en} | {title_ja} | {format}",
                    thumb_url=img,
                    description=f"{description}",
                    input_message_content=InputTextMessageContent(txt, parse_mode=ParseMode.HTML,
                                                                  disable_web_page_preview=False),
                    reply_markup=kb
                )
            )
    except Exception as e:

        kb = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Report error",
                        url="t.me/YorktownEagleUnion",
                    ),
                    InlineKeyboardButton(
                        text="Search again",
                        switch_inline_query_current_chat=".anime ",
                    ),

                ],
            ])

        results.append(

            InlineQueryResultArticle
                (
                id=str(uuid4()),
                title=f"Media {query} not found",
                input_message_content=InputTextMessageContent(f"Media {query} not found due to {e}", parse_mode=ParseMode.MARKDOWN,
                                                              disable_web_page_preview=True),
                reply_markup=kb
            )

        )

    update.inline_query.answer(results, cache_time=5)



CHAR_QUERY = '''query ($query: String) {
  Page (perPage: 15) {
        characters (search: $query) {
               id
               name {
                     first
                     middle
                     last
                     full
                     native
                     alternative
                     alternativeSpoiler
               }
               image {
                        large
                        medium
               }
               description
               gender
               dateOfBirth {
                              year
                              month
                              day
               }
               age
               siteUrl
               favourites
               modNotes
        }
    }
}'''

def character_query(query: str, update: Update, context: CallbackContext) -> None:
    """
    Handle character inline query.
    """
    results: List = []

    try:
        res = requests.post(
                    'https://graphql.anilist.co',
                    data=json.dumps({'query': CHAR_QUERY, 'variables': {'query': query}}),
                    headers={'Content-Type': 'application/json', 'Accept': 'application/json'}
              ).json()

        data = res.get('data').get('Page').get('characters')
        res = data
        for data in res:
            name = data.get('name').get('full') or query
            nati_name = data.get('name').get('native') or 'N/A'
            alt_name = data.get('name').get('alternative') or 'N/A'
            favourite = data.get('favourites') or 'N/A'
            char_age = data.get('age', 'N/A')
            char_gender = data.get('gender') or 'N/A'
            thumb_url_large = data.get('image').get('large') or "https://telegra.ph/file/cc83a0b7102ad1d7b1cb3.jpg"
            site_url = data.get('siteUrl') or "https://anilist.co/characters"

            try:
                alt_name = data.get('name').get('alternative')
                neme = ""
                for altname in alt_name:
                     neme += f"`{altname}` ,"
                alt_name = f"{neme}"
            except:
                alt_name = data.get('name').get('alternative') or "N/A"

            try:
                des = data.get("description").replace("<br>", "").replace("</br>", "")
                description = des.replace("<i>", "").replace("</i>", "") or "N/A"
            except AttributeError:
                description = data.get("description")

            if len((str(description))) > 700:
                description = description [0:700] + "....."

            txt = f"*{name}* - (*{nati_name or 'N/A'}*)\n"
            txt += f"\n*Alternative*: {alt_name or 'N/A'}"
            txt += f"\n*Favourite*: {favourite or 'N/A'}"
            txt += f"\n*Gender*: {char_gender or 'N/A'}"
            txt += f"\n*Age*: {char_age or 'N/A'}"
            txt += f"\n\n*Description*: \n{description or 'N/A'}"

            kb = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Read More",
                            url=site_url,
                        ),

                    ],
                    [
                        InlineKeyboardButton(
                            text="Search Again",
                            switch_inline_query_current_chat=".char ",
                        ),

                    ],
                ])

            results.append(InlineQueryResultArticle(
                    id=str(uuid4()),
                    title=name or query,
                    description=site_url or query,
                    thumb_url=thumb_url_large or "https://telegra.ph/file/cc83a0b7102ad1d7b1cb3.jpg",
                    input_message_content=InputTextMessageContent(txt, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=False),
                    reply_markup=kb,
                )
            )
    except Exception as e:
        log.exception(e)
        kb = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Report error",
                        url="t.me/YorktownEagleUnion",
                    ),
                    InlineKeyboardButton(
                        text="Search again",
                        switch_inline_query_current_chat=".char ",
                    ),

                ],
            ])

        results.append(

            InlineQueryResultArticle(
                id=str(uuid4()),
                title=f"Character {query} not found",
                thumb_url="https://telegra.ph/file/cc83a0b7102ad1d7b1cb3.jpg",
                input_message_content=InputTextMessageContent(f"Character {query} not found due to {e}"),
                reply_markup=kb,
            )

        )

    update.inline_query.answer(results, cache_time=5)
