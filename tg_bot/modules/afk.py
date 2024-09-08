import html
import random

from telegram import Update, MessageEntity
from telegram.ext import Filters, CallbackContext
from telegram.error import BadRequest
from tg_bot.modules.sql import afk_sql as sql
from tg_bot.modules.users import get_user_id
from tg_bot.modules.helper_funcs.decorators import kigcmd, kigmsg, rate_limit

@kigmsg(Filters.regex("(?i)^brb"), friendly="afk", group=3)
@kigcmd(command="afk", group=3)
@rate_limit(40, 60)
def afk(update: Update, context: CallbackContext):
    args = update.effective_message.text.split(None, 1)
    user = update.effective_user

    if not user:  # ignore channels
        return

    if user.id in (777000, 1087968824):
        return

    notice = ""
    if len(args) >= 2:
        reason = args[1]
        if len(reason) > 100:
            reason = reason[:100]
            notice = "\nYour afk reason was shortened to 100 characters."
    else:
        reason = ""

    sql.set_afk(update.effective_user.id, reason)
    fname = update.effective_user.first_name
    try:
        update.effective_message.reply_text("{} is now away!{}".format(fname, notice))
    except BadRequest:
        pass

@kigmsg((Filters.all & Filters.chat_type.groups & ~Filters.user(777000)), friendly='afk', group=1)
@rate_limit(40, 60)
def no_longer_afk(update: Update, context: CallbackContext):
    user = update.effective_user
    message = update.effective_message

    if not user:  # ignore channels
        return

    res = sql.rm_afk(user.id)
    if res:
        if message.new_chat_members:  # dont say msg
            return
        firstname = update.effective_user.first_name
        try:
            options = [
                "{} is here!",
                "{} is back!",
                "{} is now in the chat!",
                "{} is awake!",
                "{} is back online!",
                "{} is finally here!",
                "Welcome back! {}",
                "Where is {}?\nIn the chat!",
            ]
            chosen_option = random.choice(options)
            update.effective_message.reply_text(
                chosen_option.format(firstname), parse_mode=None
            )
        except:
            return

@kigmsg((Filters.entity(MessageEntity.MENTION) | Filters.entity(MessageEntity.TEXT_MENTION) & Filters.chat_type.groups), friendly='afk', group=8)
@rate_limit(40, 60)
def reply_afk(update: Update, context: CallbackContext):
    bot = context.bot
    message = update.effective_message
    userc = update.effective_user
    userc_id = userc.id
    if message.entities and message.parse_entities(
        [MessageEntity.TEXT_MENTION, MessageEntity.MENTION]
    ):
        entities = message.parse_entities(
            [MessageEntity.TEXT_MENTION, MessageEntity.MENTION]
        )

        chk_users = []
        for ent in entities:
            if ent.type == MessageEntity.TEXT_MENTION:
                user_id = ent.user.id
                fst_name = ent.user.first_name

                if user_id in chk_users:
                    return
                chk_users.append(user_id)

            if ent.type != MessageEntity.MENTION:
                return

            user_id = get_user_id(
                message.text[ent.offset : ent.offset + ent.length]
            )
            if not user_id:
                # Should never happen, since for a user to become AFK they must have spoken. Maybe changed username?
                return

            if user_id in chk_users:
                return
            chk_users.append(user_id)

            try:
                chat = bot.get_chat(user_id)
            except BadRequest:
                print(f"Error: Could not fetch user id {user_id} for AFK module")
                return
            fst_name = chat.first_name

            check_afk(update, context, user_id, fst_name, userc_id)

    elif message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        fst_name = message.reply_to_message.from_user.first_name
        check_afk(update, context, user_id, fst_name, userc_id)


def check_afk(update, context, user_id, fst_name, userc_id):
    if int(userc_id) == int(user_id):
        return
    afk_D = sql.check_afk_status(user_id)
    if not afk_D:
        return
    is_afk = afk_D.is_afk
    if is_afk:
        if reason := afk_D.reason:
            res = f"{html.escape(fst_name)} is afk.\nReason: <code>{html.escape(reason)}</code>"
            update.effective_message.reply_text(res, parse_mode="html")
        else:
            res = f"{fst_name} is afk"
            update.effective_message.reply_text(res, parse_mode=None)


def __gdpr__(user_id):
    sql.rm_afk(user_id)

from tg_bot.modules.language import gs

def get_help(chat):
    return gs(chat, "afk_help")

__mod_name__ = "AFK"
