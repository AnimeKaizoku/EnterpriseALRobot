import html
import time
import requests
from datetime import datetime
from io import BytesIO
from tg_bot.modules.sql.users_sql import get_user_com_chats
import tg_bot.modules.sql.antispam_sql as sql
from tg_bot import (
    DEV_USERS,
    GBAN_LOGS,
    OWNER_ID,
    SUDO_USERS,
    SUPPORT_USERS,
    SARDEGNA_USERS,
    WHITELIST_USERS,
    sw,
    dispatcher,
    log,
)
from tg_bot.modules.helper_funcs.chat_status import (
    is_user_admin,
    support_plus,
    user_admin,
)
from tg_bot.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from tg_bot.modules.helper_funcs.misc import send_to_list
from telegram import ParseMode, Update
from telegram.error import BadRequest, TelegramError
from telegram.ext import CallbackContext, Filters
from telegram.utils.helpers import mention_html
from tg_bot.modules.helper_funcs.chat_status import dev_plus
from spamwatch.errors import SpamWatchError, Error, UnauthorizedError, NotFoundError, Forbidden, TooManyRequests
from tg_bot.modules.helper_funcs.decorators import kigcmd, kigmsg

GBAN_ENFORCE_GROUP = -1

GBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to kick it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can kick group administrators",
    "Channel_private",
    "Not in the chat",
    "Can't remove chat owner",
}

UNGBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Method is available for supergroup and channel chats only",
    "Not in the chat",
    "Channel_private",
    "Chat_admin_required",
    "Peer_id_invalid",
    "User not found",
}




SPB_MODE = True


@kigcmd(command="spb")
@dev_plus
def spbtoggle(update: Update, context: CallbackContext):
    from tg_bot import SPB_MODE
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message
    print(SPB_MODE)
    if len(args) > 1:
        if args[1] in ("yes", "on"):
            SPB_MODE = True
            message.reply_animation("https://telegra.ph/file/a49e7bef1cc664eabcb26.mp4", caption="SpamProtection API bans are now enabled.\nAll hail @Intellivoid.")
        elif args[1] in ("no", "off"):
            SPB_MODE = False
            message.reply_text("SpamProtection API bans are now disabled.")
    elif SPB_MODE:
        message.reply_text("SpamProtection API bans are currently enabled.")
    else:
        message.reply_text("SpamProtection API bans are currenty disabled.")


@kigcmd(command="gban")
@support_plus
def gban(update: Update, context: CallbackContext):  # sourcery no-metrics
    bot, args = context.bot, context.args
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    log_message = ""

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(
            "You don't seem to be referring to a user or the ID specified is incorrect.."
        )
        return

    if int(user_id) in DEV_USERS:
        message.reply_text(
            "That user is part of the Union\nI can't act against our own."
        )
        return

    if int(user_id) in SUDO_USERS:
        message.reply_text(
            "I spy, with my little eye... a nation! Why are you guys turning on each other?"
        )
        return

    if int(user_id) in SUPPORT_USERS:
        message.reply_text(
            "OOOH someone's trying to gban a Sakura Nation! *grabs popcorn*"
        )
        return

    if int(user_id) in SARDEGNA_USERS:
        message.reply_text("That's a Sardegna! They cannot be banned!")
        return

    if int(user_id) in WHITELIST_USERS:
        message.reply_text("That's a Neptunia! They cannot be banned!")
        return

    if int(user_id) in (777000, 1087968824):
        message.reply_text("Huh, why would I gban Telegram bots?")
        return

    if user_id == bot.id:
        message.reply_text("You uhh...want me to kill myself?")
        return

    try:
        user_chat = bot.get_chat(user_id)
    except BadRequest as excp:
        if excp.message != "User not found":
            return

        message.reply_text("I can't seem to find this user.")
        return ""
    if user_chat.type != "private":
        message.reply_text("That's not a user!")
        return

    if sql.is_user_gbanned(user_id):

        if not reason:
            message.reply_text(
                "This user is already gbanned; I'd change the reason, but you haven't given me one..."
            )
            return

        old_reason = sql.update_gban_reason(
            user_id, user_chat.username or user_chat.first_name, reason
        )
        if old_reason:
            message.reply_text(
                "This user is already gbanned, for the following reason:\n"
                "<code>{}</code>\n"
                "I've gone and updated it with your new reason!".format(
                    html.escape(old_reason)
                ),
                parse_mode=ParseMode.HTML,
            )

        else:
            message.reply_text(
                "This user is already gbanned, but had no reason set; I've gone and updated it!"
            )

        return

    message.reply_text("On it!")

    start_time = time.time()
    datetime_fmt = "%Y-%m-%dT%H:%M"
    current_time = datetime.utcnow().strftime(datetime_fmt)

    if chat.type != "private":
        chat_origin = "<b>{} ({})</b>\n".format(html.escape(chat.title), chat.id)
    else:
        chat_origin = "<b>{}</b>\n".format(chat.id)

    log_message = (
        f"#GBANNED\n"
        f"<b>Originated from:</b> <code>{chat_origin}</code>\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>Banned User:</b> {mention_html(user_chat.id, user_chat.first_name)}\n"
        f"<b>Banned User ID:</b> <code>{user_chat.id}</code>\n"
        f"<b>Event Stamp:</b> <code>{current_time}</code>"
    )

    if reason:
        if chat.type == chat.SUPERGROUP and chat.username:
            log_message += f'\n<b>Reason:</b> <a href="https://telegram.me/{chat.username}/{message.message_id}">{reason}</a>'
        else:
            log_message += f"\n<b>Reason:</b> <code>{reason}</code>"

    if GBAN_LOGS:
        try:
            log = bot.send_message(GBAN_LOGS, log_message, parse_mode=ParseMode.HTML)
        except BadRequest as excp:
            log = bot.send_message(
                GBAN_LOGS,
                log_message
                + "\n\nFormatting has been disabled due to an unexpected error.",
            )

    else:
        send_to_list(bot, SUDO_USERS + SUPPORT_USERS, log_message, html=True)

    sql.gban_user(user_id, user_chat.username or user_chat.first_name, reason)

    chats = get_user_com_chats(user_id)
    gbanned_chats = 0

    for chat in chats:
        chat_id = int(chat)

        # Check if this group has disabled gbans
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            bot.kick_chat_member(chat_id, user_id)
            gbanned_chats += 1

        except BadRequest as excp:
            if excp.message not in GBAN_ERRORS:
                message.reply_text(f"Could not gban due to: {excp.message}")
                if GBAN_LOGS:
                    bot.send_message(
                        GBAN_LOGS,
                        f"Could not gban due to {excp.message}",
                        parse_mode=ParseMode.HTML,
                    )
                else:
                    send_to_list(
                        bot,
                        SUDO_USERS + SUPPORT_USERS,
                        f"Could not gban due to: {excp.message}",
                    )
                sql.ungban_user(user_id)
                return
        except TelegramError:
            pass

    if GBAN_LOGS:
        log.edit_text(
            log_message + f"\n<b>Chats affected:</b> <code>{gbanned_chats}</code>",
            parse_mode=ParseMode.HTML,
        )
    else:
        send_to_list(
            bot,
            SUDO_USERS + SUPPORT_USERS,
            f"Gban complete! (User banned in <code>{gbanned_chats}</code> chats)",
            html=True,
        )

    end_time = time.time()
    gban_time = round((end_time - start_time), 2)

    if gban_time > 60:
        gban_time = round((gban_time / 60), 2)
    message.reply_text("Done! Gbanned.", parse_mode=ParseMode.HTML)
    try:
        bot.send_message(
            user_id,
            "#GBAN"
            "You have been marked as Malicious and as such have been banned from any future groups we manage."
            f"\n<b>Reason:</b> <code>{html.escape(user.reason)}</code>"
            f"</b>Appeal Chat:</b> tinyurl.com/ZhongliSupport",
            parse_mode=ParseMode.HTML,
        )
    except:
        pass  # bot probably blocked by user

@kigcmd(command="ungban")
@support_plus
def ungban(update: Update, context: CallbackContext):  # sourcery no-metrics
    bot, args = context.bot, context.args
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    log_message = ""

    user_id = extract_user(message, args)

    if not user_id:
        message.reply_text(
            "You don't seem to be referring to a user or the ID specified is incorrect.."
        )
        return

    user_chat = bot.get_chat(user_id)
    if user_chat.type != "private":
        message.reply_text("That's not a user!")
        return

    if not sql.is_user_gbanned(user_id):
        message.reply_text("This user is not gbanned!")
        return

    message.reply_text(f"I'll give {user_chat.first_name} a second chance, globally.")

    start_time = time.time()
    datetime_fmt = "%Y-%m-%dT%H:%M"
    current_time = datetime.utcnow().strftime(datetime_fmt)

    if chat.type != "private":
        chat_origin = f"<b>{html.escape(chat.title)} ({chat.id})</b>\n"
    else:
        chat_origin = f"<b>{chat.id}</b>\n"

    log_message = (
        f"#UNGBANNED\n"
        f"<b>Originated from:</b> <code>{chat_origin}</code>\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>Unbanned User:</b> {mention_html(user_chat.id, user_chat.first_name)}\n"
        f"<b>Unbanned User ID:</b> <code>{user_chat.id}</code>\n"
        f"<b>Event Stamp:</b> <code>{current_time}</code>"
    )

    if GBAN_LOGS:
        try:
            log = bot.send_message(GBAN_LOGS, log_message, parse_mode=ParseMode.HTML)
        except BadRequest as excp:
            log = bot.send_message(
                GBAN_LOGS,
                log_message
                + "\n\nFormatting has been disabled due to an unexpected error.",
            )
    else:
        send_to_list(bot, SUDO_USERS + SUPPORT_USERS, log_message, html=True)

    chats = get_user_com_chats(user_id)
    ungbanned_chats = 0

    for chat in chats:
        chat_id = int(chat)

        # Check if this group has disabled gbans
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            member = bot.get_chat_member(chat_id, user_id)
            if member.status == "kicked":
                bot.unban_chat_member(chat_id, user_id)
                ungbanned_chats += 1

        except BadRequest as excp:
            if excp.message not in UNGBAN_ERRORS:
                message.reply_text(f"Could not un-gban due to: {excp.message}")
                if GBAN_LOGS:
                    bot.send_message(
                        GBAN_LOGS,
                        f"Could not un-gban due to: {excp.message}",
                        parse_mode=ParseMode.HTML,
                    )
                else:
                    bot.send_message(
                        OWNER_ID, f"Could not un-gban due to: {excp.message}"
                    )
                return
        except TelegramError:
            pass

    sql.ungban_user(user_id)

    if GBAN_LOGS:
        log.edit_text(
            log_message + f"\n<b>Chats affected:</b> {ungbanned_chats}",
            parse_mode=ParseMode.HTML,
        )
    else:
        send_to_list(bot, SUDO_USERS + SUPPORT_USERS, "un-gban complete!")

    end_time = time.time()
    ungban_time = round((end_time - start_time), 2)

    if ungban_time > 60:
        ungban_time = round((ungban_time / 60), 2)
        message.reply_text(f"Person has been un-gbanned. Took {ungban_time} min")
    else:
        message.reply_text(f"Person has been un-gbanned. Took {ungban_time} sec")

@kigcmd(command="gbanlist")
@support_plus
def gbanlist(update: Update, context: CallbackContext):
    banned_users = sql.get_gban_list()

    if not banned_users:
        update.effective_message.reply_text(
            "There aren't any gbanned users! You're kinder than I expected..."
        )
        return

    banfile = "Screw these guys.\n"
    for user in banned_users:
        banfile += f"[x] {user['name']} - {user['user_id']}\n"
        if user["reason"]:
            banfile += f"Reason: {user['reason']}\n"

    with BytesIO(str.encode(banfile)) as output:
        output.name = "gbanlist.txt"
        update.effective_message.reply_document(
            document=output,
            filename="gbanlist.txt",
            caption="Here is the list of currently gbanned users.",
        )


def check_and_ban(update, user_id, should_message=True):
    from tg_bot import SPB_MODE
    chat = update.effective_chat  # type: Optional[Chat]
    if SPB_MODE:
        try:
            apst = requests.get(f'https://api.intellivoid.net/spamprotection/v1/lookup?query={user_id}')
            api_status = apst.status_code
            if api_status == 200:
                try:
                    status = apst.json()
                    try:
                        bl_check = (status.get("results").get("attributes").get("is_blacklisted"))
                    except:
                        bl_check = False

                    if bl_check:
                        bl_res = (status.get("results").get("attributes").get("blacklist_reason"))
                        update.effective_chat.kick_member(user_id)
                        if should_message:
                            update.effective_message.reply_text(
                            f"This person was blacklisted on @SpamProtectionBot and has been removed!\nReason: <code>{bl_res}</code>",
                            parse_mode=ParseMode.HTML,
                        )
                except BaseException:
                    log.warning("Spam Protection API is unreachable.")
        except BaseException as e:
            log.info(f'SpamProtection was disabled due to {e}')
    try:
        sw_ban = sw.get_ban(int(user_id))
    except AttributeError:
        sw_ban = None
    except (SpamWatchError, Error, UnauthorizedError, NotFoundError, Forbidden, TooManyRequests) as e:
        log.warning(f" SpamWatch Error: {e}")
        sw_ban = None

    if sw_ban:
        update.effective_chat.kick_member(user_id)
        if should_message:
            update.effective_message.reply_text(
                f"This person has been detected as a spammer by @SpamWatch and has been removed!\nReason: <code>{sw_ban.reason}</code>",
                parse_mode=ParseMode.HTML,
            )
        return

    if sql.is_user_gbanned(user_id):
        update.effective_chat.kick_member(user_id)
        if should_message:
            text = (
                f"<b>Alert</b>: this user is globally banned.\n"
                f"<code>*bans them from here*</code>.\n"
                f"<b>Appeal chat</b>: tinyurl.com/ZhongliSupport\n"
                f"<b>User ID</b>: <code>{user_id}</code>"
            )
            user = sql.get_gbanned_user(user_id)
            if user.reason:
                text += f"\n<b>Ban Reason:</b> <code>{html.escape(user.reason)}</code>"
            update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)

@kigmsg((Filters.all & Filters.chat_type.groups), can_disable=False, group=GBAN_ENFORCE_GROUP)
def enforce_gban(update: Update, context: CallbackContext):
    # Not using @restrict handler to avoid spamming - just ignore if cant gban.
    bot = context.bot
    if (
        sql.does_chat_gban(update.effective_chat.id)
        and update.effective_chat.get_member(bot.id).can_restrict_members
    ):
        user = update.effective_user
        chat = update.effective_chat
        msg = update.effective_message

        if user and not is_user_admin(chat, user.id):
            check_and_ban(update, user.id)
            return

        if msg.new_chat_members:
            new_members = update.effective_message.new_chat_members
            for mem in new_members:
                check_and_ban(update, mem.id)

        if msg.reply_to_message:
            user = msg.reply_to_message.from_user
            if user and not is_user_admin(chat, user.id):
                check_and_ban(update, user.id, should_message=False)

@kigcmd(command="antispam")
@user_admin
def gbanstat(update: Update, context: CallbackContext):
    args = context.args
    if len(args) > 0:
        if args[0].lower() in ["on", "yes"]:
            sql.enable_gbans(update.effective_chat.id)
            update.effective_message.reply_text(
                "I've enabled gbans in this group. This will help protect you "
                "from spammers, unsavoury characters, and the biggest trolls."
            )
        elif args[0].lower() in ["off", "no"]:
            sql.disable_gbans(update.effective_chat.id)
            update.effective_message.reply_text(
                "I've disabled gbans in this group. GBans wont affect your users "
                "anymore. You'll be less protected from any trolls and spammers "
                "though!"
            )
    else:
        update.effective_message.reply_text(
            "Give me some arguments to choose a setting! on/off, yes/no!\n\n"
            "Your current setting is: {}\n"
            "When True, any gbans that happen will also happen in your group. "
            "When False, they won't, leaving you at the possible mercy of "
            "spammers.".format(sql.does_chat_gban(update.effective_chat.id))
        )


def __stats__():
    return f"• {sql.num_gbanned_users()} gbanned users."


def __user_info__(user_id):
    if user_id in (777000, 1087968824):
        return ""

    is_gbanned = sql.is_user_gbanned(user_id)
    text = "Gbanned: <b>{}</b>"
    if user_id in [777000, 1087968824]:
        return ""
    if user_id == dispatcher.bot.id:
        return ""
    if int(user_id) in SUDO_USERS + SARDEGNA_USERS + WHITELIST_USERS:
        return ""
    if is_gbanned:
        text = text.format("Yes")
        user = sql.get_gbanned_user(user_id)
        if user.reason:
            text += f"\n<b>Reason:</b> <code>{html.escape(user.reason)}</code>"
        text += f"\n<b>Appeal Chat:</b> tinyurl.com/ZhongliSupport"
    else:
        text = text.format("No")
    return text


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return f"This chat is enforcing *gbans*: `{sql.does_chat_gban(chat_id)}`."


from tg_bot.modules.language import gs

def get_help(chat):
    return gs(chat, "antispam_help")

__mod_name__ = 'AntiSpam'
