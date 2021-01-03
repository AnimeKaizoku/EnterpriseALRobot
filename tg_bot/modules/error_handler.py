import traceback
import requests
import html
import random

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, CommandHandler

from tg_bot import dispatcher, DEV_USERS, OWNER_ID


class ErrorsDict(dict):
    "A custom dict to store errors and their count"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __contains__(self, error):
        error.identifier = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=5))
        for e in self:
            if type(e) is type(error) and e.args == error.args:
                self[e] += 1
                return True
        self[error] = 0
        return False


errors = ErrorsDict()


def error_callback(update: Update, context: CallbackContext):
    if not update:
        return
    if context.error in errors:
        return
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb = "".join(tb_list)
    pretty_message = (
        "An exception was raised while handling an update\n"
        "User: {}\n"
        "Chat: {} {}\n"
        "Callback data: {}\n"
        "Message: {}\n\n"
        "Full Traceback: {}"
    ).format(
        update.effective_user.id,
        update.effective_chat.title if update.effective_chat else "",
        update.effective_chat.id if update.effective_chat else "",
        update.callback_query.data if update.callback_query else "None",
        update.effective_message.text if update.effective_message else "No message",
        tb,
    )
    key = requests.post(
        "https://nekobin.com/api/documents", json={"content": pretty_message}
    ).json()
    e = html.escape(f"{context.error}")
    if not key.get("result", {}).get("key"):
        with open("error.txt", "w+") as f:
            f.write(pretty_message)
        context.bot.send_document(
            OWNER_ID,
            open("error.txt", "rb"),
            caption=f"#{context.error.identifier}\n<b>Your sugar mommy got an error for you, you cute guy:</b>\n<code>{e}</code>",
            parse_mode="html",
        )
        return
    key = key.get("result").get("key")
    url = f"https://nekobin.com/{key}.py"
    context.bot.send_message(
        OWNER_ID,
        text=f"#{context.error.identifier}\n<b>Your sugar mommy got an error for you, you cute guy:</b>\n<code>{e}</code>",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Nekobin", url=url)]]),
        parse_mode="html",
    )


def list_errors(update: Update, context: CallbackContext):
    if update.effective_user.id not in DEV_USERS:
        return
    e = dict(sorted(errors.items(), key=lambda item: item[1], reverse=True))
    msg = "<b>Errors List:</b>\n"
    for x in e:
        msg += f"• <code>{x}:</code> <b>{e[x]}</b> #{x.identifier}\n"
    update.effective_message.reply_text(msg, parse_mode="html")


dispatcher.add_error_handler(error_callback)
dispatcher.add_handler(CommandHandler("errors", list_errors))
