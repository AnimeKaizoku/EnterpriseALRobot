import html
import json
import os
from typing import List, Optional

from telegram import Update, ParseMode, TelegramError
from telegram.ext import CommandHandler, run_async, CallbackContext
from telegram.utils.helpers import mention_html

from tg_bot import (
    dispatcher,
    WHITELIST_USERS,
    SARDEGNA_USERS,
    SUPPORT_USERS,
    SUDO_USERS,
    DEV_USERS,
    OWNER_ID,
)
from tg_bot.modules.helper_funcs.chat_status import whitelist_plus, dev_plus, sudo_plus
from tg_bot.modules.helper_funcs.extraction import extract_user
from tg_bot.modules.log_channel import gloggable

ELEVATED_USERS_FILE = os.path.join(os.getcwd(), "tg_bot/elevated_users.json")


def check_user_id(user_id: int, context: CallbackContext) -> Optional[str]:
    bot = context.bot
    if not user_id:
        reply = "That...is a chat! baka ka omae?"

    elif user_id == bot.id:
        reply = "This does not work that way."

    else:
        reply = None
    return reply


# I added extra new lines
nations = """ Kigyō has bot access levels we call as *"Nation Levels"*
\n*Eagle Union* - Devs who can access the bots server and can execute, edit, modify bot code. Can also manage other Nations
\n*God* - Only one exists, bot owner. 
Owner has complete bot access, including bot adminship in chats Kigyō is at.
\n*Royals* - Have super user access, can gban, manage Nations lower than them and are admins in Kigyō.
\n*Sakuras* - Have access go globally ban users across Kigyō.
\n*Sardegnas* - Same as Neptunians but can unban themselves if banned.
\n*Neptunians* - Cannot be banned, muted flood kicked but can be manually banned by admins.
\n*Disclaimer*: The Nation levels in Kigyō are there for troubleshooting, support, banning potential scammers.
Report abuse or ask us more on these at [Eagle Union](https://t.me/YorktownEagleUnion).
"""


def send_nations(update):
    update.effective_message.reply_text(
        nations, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
    )


@whitelist_plus
def whitelistlist(update: Update, context: CallbackContext):
    bot = context.bot
    reply = "<b>Known Neptunia Nations :</b>\n"
    for each_user in WHITELIST_USERS:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)

            reply += f"• {mention_html(user_id, user.first_name)}\n"
        except TelegramError:
            pass
    update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)


@whitelist_plus
def Sardegnalist(update: Update, context: CallbackContext):
    bot = context.bot
    reply = "<b>Known Sardegna Nations :</b>\n"
    for each_user in SARDEGNA_USERS:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            reply += f"• {mention_html(user_id, user.first_name)}\n"
        except TelegramError:
            pass
    update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)


@whitelist_plus
def supportlist(update: Update, context: CallbackContext):
    bot = context.bot
    reply = "<b>Known Sakura Nations :</b>\n"
    for each_user in SUPPORT_USERS:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            reply += f"• {mention_html(user_id, user.first_name)}\n"
        except TelegramError:
            pass
    update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)


@whitelist_plus
def sudolist(update: Update, context: CallbackContext):
    bot = context.bot
    true_sudo = list(set(SUDO_USERS) - set(DEV_USERS))
    reply = "<b>Known Royal Nations :</b>\n"
    for each_user in true_sudo:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            reply += f"• {mention_html(user_id, user.first_name)}\n"
        except TelegramError:
            pass
    update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)


@whitelist_plus
def devlist(update: Update, context: CallbackContext):
    bot = context.bot
    true_dev = list(set(DEV_USERS) - {OWNER_ID})
    reply = "<b>Eagle Union Members :</b>\n"
    for each_user in true_dev:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            reply += f"• {mention_html(user_id, user.first_name)}\n"
        except TelegramError:
            pass
    update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)


__help__ = """
 - /eagle - Lists all Hero Union members.
 - /royals - Lists all Royal Nations.
 - /sakuras - Lists all Sakura Nations.
 - /sardegnas - Lists all Sardegnas Nations.
 - /neptunians - Lists all Neptunia Nations.
 Note: These commands list users with special bot priveleges and can only be used by them.
 You can visit @YorktownEagleUnion to query more about these.
"""

WHITELISTLIST_HANDLER = CommandHandler(
    ["whitelistlist", "neptunians"], whitelistlist, run_async=True
)
SARDEGNALIST_HANDLER = CommandHandler(["sardegnas"], Sardegnalist, run_async=True)
SUPPORTLIST_HANDLER = CommandHandler(
    ["supportlist", "sakuras"], supportlist, run_async=True
)
SUDOLIST_HANDLER = CommandHandler(["sudolist", "royals"], sudolist, run_async=True)
DEVLIST_HANDLER = CommandHandler(["devlist", "eagle"], devlist, run_async=True)

dispatcher.add_handler(WHITELISTLIST_HANDLER)
dispatcher.add_handler(SARDEGNALIST_HANDLER)
dispatcher.add_handler(SUPPORTLIST_HANDLER)
dispatcher.add_handler(SUDOLIST_HANDLER)
dispatcher.add_handler(DEVLIST_HANDLER)

__mod_name__ = "Nations"
__handlers__ = [
    WHITELISTLIST_HANDLER,
    SARDEGNALIST_HANDLER,
    SUPPORTLIST_HANDLER,
    SUDOLIST_HANDLER,
    DEVLIST_HANDLER,
]
