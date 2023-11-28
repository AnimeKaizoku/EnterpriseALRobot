import contextlib
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
from tg_bot.modules.helper_funcs.decorators import kiginline, rate_limit


def remove_prefix(text, prefix):
    if text.startswith(prefix):
        text = text.replace(prefix, "", 1)
    return text

@kiginline()
@rate_limit(40, 60)
def inlinequery(update: Update, _) -> None:
    """
    Main InlineQueryHandler callback.
    """
    query = update.inline_query.query
    user = update.effective_user

    results: List = []
    inline_funcs = {
        # ".spb": spb,
        ".info": inlineinfo,
        ".about": about,
        ".anilist": media_query,
    }

    if (f := query.split(" ", 1)[0]) in inline_funcs:
        inline_funcs[f](remove_prefix(query, f).strip(), update, user)
    else:
        inline_help_dicts = [
            # {
            #    "title": "SpamProtection INFO",
            #    "description": "Look up a person/bot/channel/chat on @Intellivoid SpamProtection API",
            #    "message_text": "Click the button below to look up a person/bot/channel/chat on @Intellivoid SpamProtection API using "
            #                    "username or telegram id",
            #    "thumb_urL": "https://telegra.ph/file/3ce9045b1c7faf7123c67.jpg",
            #    "keyboard": ".spb ",
            #},
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
                "title": "Anilist",
                "description": "Search anime and manga on AniList.co",
                "message_text": "Click the button below to search anime and manga on AniList.co",
                "thumb_urL": "https://telegra.ph/file/c85e07b58f5b3158b529a.jpg",
                "keyboard": ".anilist ",
            },
        ]

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
        text += "\\n\\nThis person is my owner"
        nation_level_present = True
    elif user.id in DEV_USERS:
        text += "\\n\\nThis Person is a part of Eagle Union"
        nation_level_present = True
    elif user.id in SUDO_USERS:
        text += "\\n\\nThe Nation level of this person is Royal"
        nation_level_present = True
    elif user.id in SUPPORT_USERS:
        text += "\\n\\nThe Nation level of this person is Sakura"
        nation_level_present = True
    elif user.id in SARDEGNA_USERS:
        text += "\\n\\nThe Nation level of this person is Sardegna"
        nation_level_present = True
    elif user.id in WHITELIST_USERS:
        text += "\\n\\nThe Nation level of this person is Neptunia"
        nation_level_present = True

    if nation_level_present:
        text += f' [<a href="https://t.me/{bot.username}?start=nations">?</a>]'

    with contextlib.suppress(Exception):
        if spamwtc := sw.get_ban(int(user.id)):
            text += "<b>\n\n• SpamWatched:\n</b> Yes"
            text += f"\n• Reason: <pre>{spamwtc.reason}</pre>"
            text += "\n• Appeal at @SpamWatchSupport"
        else:
            text += "<b>\n\n• SpamWatched:</b> No"
    num_chats = sql.get_user_num_chats(user.id)
    text += f"\n• <b>Chat count</b>: <code>{num_chats}</code>"




    kb = InlineKeyboardMarkup([[InlineKeyboardButton(text="Report Error", url="https://t.me/YorktownEagleUnion"), InlineKeyboardButton(text="Search again", switch_inline_query_current_chat=".info ",)]])


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
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(text="Support", url="https://t.me/YorktownEagleUnion"), InlineKeyboardButton(text="Channel", url="https://t.me/KigyoUpdates"), InlineKeyboardButton(text='Ping', callback_data='pingCB')], [InlineKeyboardButton(text="GitLab", url="https://www.gitlab.com/Dank-del/EnterpriseALRobot"), InlineKeyboardButton(text="GitHub", url="https://github.com/AnimeKaizoku/EnterpriseALRobot/",)]])


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
    # sourcery skip: avoid-builtin-shadow
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
                description = f'{description[:700]}.....'

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
                            switch_inline_query_current_chat=".anilist ",
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
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(text="Report error", url="t.me/YorktownEagleUnion"), InlineKeyboardButton(text="Search again", switch_inline_query_current_chat=".anilist ")]])

        results.append(InlineQueryResultArticle(id=str(uuid4()), title=f"Media {query} not found", input_message_content=InputTextMessageContent(f"Media {query} not found due to {e}", parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True), reply_markup=kb))

    update.inline_query.answer(results, cache_time=5)
