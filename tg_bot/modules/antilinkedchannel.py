import html

from telegram import Update, TelegramError
from telegram.ext import CallbackContext
from telegram.ext.filters import Filters

from tg_bot.modules.helper_funcs.decorators import kigcmd, kigmsg
from ..modules.helper_funcs.anonymous import user_admin, AdminPerms
import tg_bot.modules.sql.antilinkedchannel_sql as sql


@kigcmd(command="antilinkedchan", group=112)
@user_admin(AdminPerms.CAN_RESTRICT_MEMBERS)
def set_antilinkedchannel(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    args = context.args
    if len(args) > 0:
        s = args[0].lower()
        if s in ["yes", "on"]:
            sql.enable(chat.id)
            message.reply_html("Enabled anti linked channel in {}".format(html.escape(chat.title)))
        elif s in ["off", "no"]:
            sql.disable(chat.id)
            message.reply_html("Disabled anti linked channel in {}".format(html.escape(chat.title)))
        else:
            message.reply_text("Unrecognized arguments {}".format(s))
        return
    message.reply_html(
        "Linked channel deletion is currently {} in {}".format(sql.status(chat.id), html.escape(chat.title)))


@kigmsg(Filters.is_automatic_forward, group=111)
def eliminate_linked_channel_msg(update: Update, _: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    if not sql.status(chat.id):
        return
    try:
        message.delete()
    except TelegramError:
        return
