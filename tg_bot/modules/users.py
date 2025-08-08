import contextlib
from io import BytesIO
from time import sleep
import time
from tg_bot.modules.helper_funcs.decorators import rate_limit

import tg_bot.modules.sql.users_sql as sql
from tg_bot import DEV_USERS, log, OWNER_ID, dispatcher, redis_conn
from tg_bot.modules.helper_funcs.chat_status import dev_plus, sudo_plus
from tg_bot.modules.sql.users_sql import get_all_users
from telegram import TelegramError, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, Filters, MessageHandler, ChatMemberHandler

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
@rate_limit(40, 60)
def broadcast(update: Update, context: CallbackContext):
    to_send = update.effective_message.text.split(None, 1)

    if len(to_send) >= 2:
        cmd = to_send[0]
        msg_text = to_send[1]
        to_group = cmd == "/broadcastgroups" or cmd == "/broadcastall"
        to_user = cmd == "/broadcastusers" or cmd == "/broadcastall"
        if cmd not in ["/broadcastgroups", "/broadcastusers", "/broadcastall"]:
            to_group = to_user = True
        meta_key = "broadcast:meta"
        lock_key = "broadcast:lock"
        gq_key = "broadcast:groups"
        uq_key = "broadcast:users"
        existing = redis_conn.hgetall(meta_key)
        if existing and existing.get(b"status", b"").decode() in ["running", "paused"]:
            update.effective_message.reply_text("A broadcast is in progress. Use /broadcaststatus or /broadcastresume.")
            return
        if to_group:
            redis_conn.delete(gq_key)
            for c in sql.get_all_chats() or []:
                redis_conn.rpush(gq_key, int(c))
        if to_user:
            redis_conn.delete(uq_key)
            for u in get_all_users() or []:
                redis_conn.rpush(uq_key, int(u))
        total_groups = redis_conn.llen(gq_key) if to_group else 0
        total_users = redis_conn.llen(uq_key) if to_user else 0
        redis_conn.hmset(
            meta_key,
            {
                "message": msg_text,
                "to_group": int(to_group),
                "to_user": int(to_user),
                "total_groups": int(total_groups),
                "total_users": int(total_users),
                "sent_groups": 0,
                "sent_users": 0,
                "failed_groups": 0,
                "failed_users": 0,
                "status": "paused",
                "admin_id": update.effective_user.id,
                "started_at": int(time.time()),
                "updated_at": int(time.time()),
            },
        )
        if not redis_conn.set(lock_key, str(int(time.time())), nx=True, ex=3600):
            update.effective_message.reply_text("Another broadcast is running. Try again later.")
            return
        redis_conn.hset(meta_key, "status", "running")
        failed_g = 0
        failed_u = 0
        if to_group:
            while True:
                nxt = redis_conn.lpop(gq_key)
                if not nxt:
                    break
                try:
                    context.bot.sendMessage(
                        int(nxt),
                        msg_text,
                        parse_mode="MARKDOWN",
                        disable_web_page_preview=True,
                    )
                    redis_conn.hincrby(meta_key, "sent_groups", 1)
                except TelegramError:
                    failed_g += 1
                    redis_conn.hincrby(meta_key, "failed_groups", 1)
                redis_conn.hset(meta_key, "updated_at", int(time.time()))
                redis_conn.expire(lock_key, 3600)
                sleep(0.1)
        if to_user:
            while True:
                nxt = redis_conn.lpop(uq_key)
                if not nxt:
                    break
                try:
                    context.bot.sendMessage(
                        int(nxt),
                        msg_text,
                        parse_mode="MARKDOWN",
                        disable_web_page_preview=True,
                    )
                    redis_conn.hincrby(meta_key, "sent_users", 1)
                except TelegramError:
                    failed_u += 1
                    redis_conn.hincrby(meta_key, "failed_users", 1)
                redis_conn.hset(meta_key, "updated_at", int(time.time()))
                redis_conn.expire(lock_key, 3600)
                sleep(0.1)
        redis_conn.hset(meta_key, "status", "completed")
        redis_conn.delete(lock_key)
        update.effective_message.reply_text(
            f"Broadcast complete.\nGroups failed: {failed_g}.\nUsers failed: {failed_u}."
        )


@dev_plus
@rate_limit(20, 30)
def broadcast_status(update: Update, context: CallbackContext):
    meta = redis_conn.hgetall("broadcast:meta")
    if not meta:
        update.effective_message.reply_text("No broadcast state.")
        return
    m = {k.decode(): v.decode() for k, v in meta.items()}
    tg = int(m.get("total_groups", 0) or 0)
    tu = int(m.get("total_users", 0) or 0)
    sg = int(m.get("sent_groups", 0) or 0)
    su = int(m.get("sent_users", 0) or 0)
    fg = int(m.get("failed_groups", 0) or 0)
    fu = int(m.get("failed_users", 0) or 0)
    rg = redis_conn.llen("broadcast:groups") if int(m.get("to_group", 0)) else 0
    ru = redis_conn.llen("broadcast:users") if int(m.get("to_user", 0)) else 0
    status = m.get("status", "unknown")
    update.effective_message.reply_text(
        f"Status: {status}\nGroups: {sg}/{tg} (left {rg}), failed {fg}\nUsers: {su}/{tu} (left {ru}), failed {fu}"
    )


@dev_plus
@rate_limit(40, 60)
def broadcast_resume(update: Update, context: CallbackContext):
    meta_key = "broadcast:meta"
    lock_key = "broadcast:lock"
    gq_key = "broadcast:groups"
    uq_key = "broadcast:users"
    meta = redis_conn.hgetall(meta_key)
    if not meta:
        update.effective_message.reply_text("No broadcast to resume.")
        return
    m = {k.decode(): v.decode() for k, v in meta.items()}
    if m.get("status") == "completed" or (redis_conn.llen(gq_key) == 0 and redis_conn.llen(uq_key) == 0):
        update.effective_message.reply_text("Broadcast already completed.")
        return
    if not redis_conn.set(lock_key, str(int(time.time())), nx=True, ex=3600):
        update.effective_message.reply_text("Another broadcast is running. Try again later.")
        return
    redis_conn.hset(meta_key, "status", "running")
    msg_text = m.get("message", "")
    to_group = bool(int(m.get("to_group", 0)))
    to_user = bool(int(m.get("to_user", 0)))
    failed_g = 0
    failed_u = 0
    if to_group:
        while True:
            nxt = redis_conn.lpop(gq_key)
            if not nxt:
                break
            try:
                context.bot.sendMessage(
                    int(nxt),
                    msg_text,
                    parse_mode="MARKDOWN",
                    disable_web_page_preview=True,
                )
                redis_conn.hincrby(meta_key, "sent_groups", 1)
            except TelegramError:
                failed_g += 1
                redis_conn.hincrby(meta_key, "failed_groups", 1)
            redis_conn.hset(meta_key, "updated_at", int(time.time()))
            redis_conn.expire(lock_key, 3600)
            sleep(0.1)
    if to_user:
        while True:
            nxt = redis_conn.lpop(uq_key)
            if not nxt:
                break
            try:
                context.bot.sendMessage(
                    int(nxt),
                    msg_text,
                    parse_mode="MARKDOWN",
                    disable_web_page_preview=True,
                )
                redis_conn.hincrby(meta_key, "sent_users", 1)
            except TelegramError:
                failed_u += 1
                redis_conn.hincrby(meta_key, "failed_users", 1)
            redis_conn.hset(meta_key, "updated_at", int(time.time()))
            redis_conn.expire(lock_key, 3600)
            sleep(0.1)
    redis_conn.hset(meta_key, "status", "completed")
    redis_conn.delete(lock_key)
    update.effective_message.reply_text(
        f"Broadcast complete.\nGroups failed: {failed_g}.\nUsers failed: {failed_u}."
    )


def welcomeFilter(update: Update, context: CallbackContext):
    if update.effective_chat.type not in ["group", "supergroup"]:
        return
    if nm := update.chat_member.new_chat_member:
        om = update.chat_member.old_chat_member
    if (nm.status, om.status) in [(nm.MEMBER, nm.KICKED), (nm.MEMBER, nm.LEFT), (nm.KICKED, nm.MEMBER), 
                                  (nm.KICKED, nm.ADMINISTRATOR), (nm.KICKED, nm.CREATOR), (nm.LEFT, nm.MEMBER), 
                                  (nm.LEFT, nm.ADMINISTRATOR), (nm.LEFT, nm.CREATOR)]:
        return log_user(update, context)

@rate_limit(30, 60)
def log_user(update: Update, _: CallbackContext):
    chat = update.effective_chat
    msg = update.effective_message
    
    if not msg and update.chat_member: # ChatMemberUpdate for join/leave
        sql.update_user(update.effective_user.id, update.effective_user.username, chat.id, chat.title)
        return

    sql.update_user(msg.from_user.id, msg.from_user.username, chat.id, chat.title)

    if rep := msg.reply_to_message:
        sql.update_user(
            rep.from_user.id,
            rep.from_user.username,
            chat.id,
            chat.title,
        )

        if rep.forward_from:
            sql.update_user(
                rep.forward_from.id,
                rep.forward_from.username,
            )

        if rep.entities:
            for entity in rep.entities:
                if entity.type in ["text_mention", "mention"]:
                    with contextlib.suppress(AttributeError):
                        sql.update_user(entity.user.id, entity.user.username)
        if rep.sender_chat and not rep.is_automatic_forward:
            sql.update_user(
                rep.sender_chat.id,
                rep.sender_chat.username,
                chat.id,
                chat.title,
            )

    if msg.forward_from:
        sql.update_user(msg.forward_from.id, msg.forward_from.username)

    if msg.entities:
        for entity in msg.entities:
            if entity.type in ["text_mention", "mention"]:
                with contextlib.suppress(AttributeError):
                    sql.update_user(entity.user.id, entity.user.username)
    if msg.sender_chat and not msg.is_automatic_forward:
        sql.update_user(msg.sender_chat.id, msg.sender_chat.username, chat.id, chat.title)

    if msg.new_chat_members:
        for user in msg.new_chat_members:
            if user.id == msg.from_user.id:  # we already added that in the first place
                continue
            sql.update_user(user.id, user.username, chat.id, chat.title)


@sudo_plus
@rate_limit(40, 60)
def chats(update: Update, context: CallbackContext):
    all_chats = sql.get_all_chats() or []
    chatfile = "List of chats.\n0. Chat name | Chat ID | Members count\n"
    P = 1
    for chat in all_chats:
        try:
            curr_chat = context.bot.getChat(chat.chat_id)
            bot_member = curr_chat.get_member(context.bot.id)
            chat_members = curr_chat.get_member_count(context.bot.id)
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

@rate_limit(50, 60)
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
BROADCST_STATUS_HANDLER = CommandHandler(
    ["broadcaststatus"], broadcast_status, run_async=True
)
BROADCST_RESUME_HANDLER = CommandHandler(
    ["broadcastresume"], broadcast_resume, run_async=True
)
USER_HANDLER = MessageHandler(
    Filters.all & Filters.chat_type.groups & ~Filters.user(777000), log_user, run_async=True
)
CHAT_CHECKER_HANDLER = MessageHandler(
    Filters.all & Filters.chat_type.groups & ~Filters.user(777000), chat_checker, run_async=True
)
# CHATLIST_HANDLER = CommandHandler("chatlist", chats, run_async=True)

dispatcher.add_handler(
    ChatMemberHandler(
        welcomeFilter, ChatMemberHandler.CHAT_MEMBER, run_async=True
    ), group=110)

dispatcher.add_handler(USER_HANDLER, USERS_GROUP)
dispatcher.add_handler(BROADCAST_HANDLER)
dispatcher.add_handler(BROADCST_STATUS_HANDLER)
dispatcher.add_handler(BROADCST_RESUME_HANDLER)
# dispatcher.add_handler(CHATLIST_HANDLER)
dispatcher.add_handler(CHAT_CHECKER_HANDLER, CHAT_GROUP)

__mod_name__ = "Users"
__handlers__ = [(USER_HANDLER, USERS_GROUP), BROADCAST_HANDLER, BROADCST_STATUS_HANDLER, BROADCST_RESUME_HANDLER]
