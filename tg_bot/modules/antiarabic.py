# Create file by @FFmpegNotInstalled

from typing import List

from telegram import Update, Bot, ParseMode
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, Filters
from telegram.ext.dispatcher import run_async

from tg_bot import dispatcher
from .helper_funcs.chat_status import user_not_admin, user_admin, can_delete
from .helper_funcs.extraction import extract_text
from .sql import antiArabic_sql as sql

ANTIARABIC_GROUPS = 12

@run_async
@user_admin
def antiarabic_setting(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user
    member = chat.get_member(int(user.id))

    if chat.type != chat.PRIVATE:
        if len(args) >= 1:
            if args[0].lower() in ("yes", "on", "true"):
                sql.set_chat_setting(chat.id, True)
                msg.reply_text("Turned on AntiArabic! Messages sent by any non-admin which contains arabic text will be deleted.")

            elif args[0].lower() in ("no", "off", "false"):
                sql.set_chat_setting(chat.id, False)
                msg.reply_text("Turned off AntiArabic! Messages containing arabic text won't be deleted.")
        else:
           msg.reply_text("</antiarabic on/off> to turn on or turn off AntiArabic Mode.").format(
                sql.chat_antiarabic(chat.id),
                parse_mode=ParseMode.MARKDOWN)


@user_not_admin
@run_async
def antiarabic(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    msg = update.effective_message
    to_match = extract_text(msg)
    user = update.effective_user
    has_arabic = False

    if not sql.chat_antiarabic(chat.id):
        return ""

    if not user:  # ignore channels
        return ""

    if user.id == 777000:  # ignore telegram
        return ""

    if not to_match:
        return

    if chat.type != chat.PRIVATE:
        for c in to_match:
            if ('\u0600' <= c <= '\u06FF' or '\u0750' <= c <= '\u077F'
                    or '\u08A0' <= c <= '\u08FF' or '\uFB50' <= c <= '\uFDFF'
                    or '\uFE70' <= c <= '\uFEFF'
                    or '\U00010E60' <= c <= '\U00010E7F'
                    or '\U0001EE00' <= c <= '\U0001EEFF'):
                if can_delete(chat, bot.id):
                    update.effective_message.delete()
                    return ""


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)

from .language import gs

def get_help(chat):
    return gs(chat, "antiarabic_help")

SETTING_HANDLER = CommandHandler("antiarabic", antiarabic_setting,
                                 pass_args=True)
ANTI_ARABIC = MessageHandler(
    (Filters.text | Filters.command | Filters.sticker | Filters.photo) & Filters.group, antiarabic)

dispatcher.add_handler(SETTING_HANDLER)
dispatcher.add_handler(ANTI_ARABIC, group=ANTIARABIC_GROUPS)

__mod_name__ = "Anti Arabic"
