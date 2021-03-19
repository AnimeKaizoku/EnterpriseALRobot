from uuid import uuid4
import html
from telegram.utils.helpers import mention_html
from telegram.error import BadRequest
from telegram import InlineQueryResultArticle, ParseMode, InputTextMessageContent, Update
from telegram.ext import Updater, InlineQueryHandler, CommandHandler, CallbackContext
from telegram.utils.helpers import escape_markdown
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
from tg_bot.modules.helper_funcs.extraction import extract_user
from tg_bot.__main__ import USER_INFO
import tg_bot.modules.sql.users_sql as sql
from spamprotection.sync import SPBClient
from spamprotection.errors import HostDownError
client = SPBClient()

def inlineinfo(update: Update, context: CallbackContext) -> None:
    """Handle the inline query."""
    bot, args = context.bot, context.args
    query = update.inline_query.query
    log.info(query)
    user_id = update.effective_user.id
    search = query.split(" ", 1)[1]
    try:
        user = bot.get_chat(int(search))
    except BadRequest:
        user = bot.get_chat(user_id)

    chat = update.effective_chat
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
        text += f"<b>Ham Prediction ID:</b> <code>{hamp}</code>\n"
        text += f"<b>Potential Spammer:</b> <code>{ps}</code>\n"
        text += f"<b>Blacklisted:</b> <code>{blc}</code>\n"
        text += f"<b>Blacklist Reason:</b> <code>{blres}</code>\n"
    except HostDownError:
        text += "\n\n<b>SpamProtection:</b>"
        text += "\nCan't connect to Intellivoid SpamProtection API\n"

    Nation_level_present = False

    num_chats = sql.get_user_num_chats(user.id)
    text += f"\nChat count: <code>{num_chats}</code>"

    if user.id == OWNER_ID:
        text += f"\nThis person is my owner"
        Nation_level_present = True
    elif user.id in DEV_USERS:
        text += f"\nThis Person is a part of Eagle Union"
        Nation_level_present = True
    elif user.id in SUDO_USERS:
        text += f"\nThe Nation level of this person is Royal"
        Nation_level_present = True
    elif user.id in SUPPORT_USERS:
        text += f"\nThe Nation level of this person is Sakura"
        Nation_level_present = True
    elif user.id in SARDEGNA_USERS:
        text += f"\nThe Nation level of this person is Sardegna"
        Nation_level_present = True
    elif user.id in WHITELIST_USERS:
        text += f"\nThe Nation level of this person is Neptunia"
        Nation_level_present = True

    if Nation_level_present:
        text += ' [<a href="https://t.me/{}?start=nations">?</a>]'.format(bot.username)


    results = [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title=f"User info of {html.escape(user.first_name)}",
            input_message_content=InputTextMessageContent(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True),
        ),
        ]

    update.inline_query.answer(results, cache_time=5)

dispatcher.add_handler(InlineQueryHandler(inlineinfo, pattern="info .*"))
