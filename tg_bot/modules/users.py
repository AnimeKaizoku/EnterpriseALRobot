from io import BytesIO
from time import sleep

import tg_bot.modules.sql.users_sql as sql
from tg_bot import DEV_USERS, log, OWNER_ID, dispatcher
from tg_bot.modules.helper_funcs.chat_status import dev_plus, sudo_plus
from tg_bot.modules.sql.users_sql import get_all_users
from telegram import TelegramError, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, Filters, MessageHandler

USERS_GROUP = 4
CHAT_GROUP = 5
DEV_AND_MORE = DEV_USERS.append(int(OWNER_ID))


def get_user_id(username):
    # ensure valid userid
    if len(username) <= 5:
        return None

    if username.startswith("@"):
        username = username[1:]

    users = sql.get_userid_by_name(username)

    if not users:
        return None

    elif len(users) == 1:
        return users[0].user_id

    else:
        for user_obj in users:
            try:
                userdat = dispatcher.bot.get_chat(user_obj.user_id)
                if userdat.username == username:
                    return userdat.id

            except BadRequest as excp:
                if excp.message != "Chat not found":
                    log.exception("Error extracting user ID")

    return None


@dev_plus
def broadcast(update: Update, context: CallbackContext):
    to_send = update.effective_message.text.split(None, 1)

    if len(to_send) >= 2:
        to_group = False
        to_user = False
        if to_send[0] == "/broadcastgroups":
            to_group = True
        if to_send[0] == "/broadcastusers":
            to_user = True
        else:
            to_group = to_user = True
        chats = sql.get_all_chats() or []
        users = get_all_users()
        failed = 0
        failed_user = 0
        if to_group:
            for chat in chats:
                try:
                    context.bot.sendMessage(
                        int(chat.chat_id),
                        to_send[1],
                        parse_mode="MARKDOWN",
                        disable_web_page_preview=True,
                    )
                    sleep(0.1)
                except TelegramError:
                    failed += 1
        if to_user:
            for user in users:
                try:
                    context.bot.sendMessage(
                        int(user.user_id),
                        to_send[1],
                        parse_mode="MARKDOWN",
                        disable_web_page_preview=True,
                    )
                    sleep(0.1)
                except TelegramError:
                    failed_user += 1
        update.effective_message.reply_text(
            f"Broadcast complete.\nGroups failed: {failed}.\nUsers failed: {failed_user}."
        )


def log_user(update: Update, context: CallbackContext):
    chat = update.effective_chat
    msg = update.effective_message

    sql.update_user(msg.from_user.id, msg.from_user.username, chat.id, chat.title)

    if msg.reply_to_message:
        sql.update_user(
            msg.reply_to_message.from_user.id,
            msg.reply_to_message.from_user.username,
            chat.id,
            chat.title,
        )

    if msg.forward_from:
        sql.update_user(msg.forward_from.id, msg.forward_from.username)


@sudo_plus
def chats(update: Update, context: CallbackContext):
    all_chats = sql.get_all_chats() or []
    chatfile = "List of chats.\n0. Chat name | Chat ID | Members count\n"
    P = 1
    for chat in all_chats:
        try:
            curr_chat = context.bot.getChat(chat.chat_id)
            bot_member = curr_chat.get_member(context.bot.id)
            chat_members = curr_chat.get_members_count(context.bot.id)
            chatfile += "{}. {} | {} | {}\n".format(
                P, chat.chat_name, chat.chat_id, chat_members
            )
            P += 1
        except:
            pass

    with BytesIO(str.encode(chatfile)) as output:
        output.name = "glist.txt"
        update.effective_message.reply_document(
            document=output,
            filename="glist.txt",
            caption="Here be the list of groups in my database.",
        )


def chat_checker(update: Update, context: CallbackContext):
    bot = context.bot
    if update.effective_message.chat.get_member(bot.id).can_send_messages is False:
        bot.leaveChat(update.effective_message.chat.id)


def __user_info__(user_id):
    if user_id in [777000, 1087968824]:
        return """Groups count: <code>N/A</code>"""
    if user_id == dispatcher.bot.id:
        return """Groups count: <code>N/A</code>"""
    num_chats = sql.get_user_num_chats(user_id)
    return f"""Groups count: <code>{num_chats}</code>"""


def __stats__():
    return f"• {sql.num_users()} users, across {sql.num_chats()} chats"


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


__help__ = ""  # no help string

BROADCAST_HANDLER = CommandHandler(
    ["broadcastall", "broadcastusers", "broadcastgroups"], broadcast, run_async=True
)
USER_HANDLER = MessageHandler(
    Filters.all & Filters.chat_type.groups, log_user, run_async=True
)
CHAT_CHECKER_HANDLER = MessageHandler(
    Filters.all & Filters.chat_type.groups, chat_checker, run_async=True
)
CHATLIST_HANDLER = CommandHandler("chatlist", chats, run_async=True)

dispatcher.add_handler(USER_HANDLER, USERS_GROUP)
dispatcher.add_handler(BROADCAST_HANDLER)
dispatcher.add_handler(CHATLIST_HANDLER)
dispatcher.add_handler(CHAT_CHECKER_HANDLER, CHAT_GROUP)

__mod_name__ = "Users"
__handlers__ = [(USER_HANDLER, USERS_GROUP), BROADCAST_HANDLER, CHATLIST_HANDLER]
