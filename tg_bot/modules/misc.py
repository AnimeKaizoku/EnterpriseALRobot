import html
import re, os
import time
from typing import List

import requests
from telegram import Update, MessageEntity, ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters, CallbackContext
from telegram.utils.helpers import mention_html
from subprocess import Popen, PIPE

from tg_bot import (
    dispatcher,
    OWNER_ID,
    SUDO_USERS,
    SUPPORT_USERS,
    DEV_USERS,
    SARDEGNA_USERS,
    WHITELIST_USERS,
    INFOPIC,
    sw
)
from tg_bot.__main__ import STATS, USER_INFO, TOKEN
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import user_admin, sudo_plus
from tg_bot.modules.helper_funcs.extraction import extract_user
import tg_bot.modules.sql.users_sql as sql

MARKDOWN_HELP = f"""
Markdown is a very powerful formatting tool supported by telegram. {dispatcher.bot.first_name} has some enhancements, to make sure that \
saved messages are correctly parsed, and to allow you to create buttons.

- <code>_italic_</code>: wrapping text with '_' will produce italic text
- <code>*bold*</code>: wrapping text with '*' will produce bold text
- <code>`code`</code>: wrapping text with '`' will produce monospaced text, also known as 'code'
- <code>[sometext](someURL)</code>: this will create a link - the message will just show <code>sometext</code>, \
and tapping on it will open the page at <code>someURL</code>.
EG: <code>[test](example.com)</code>

- <code>[buttontext](buttonurl:someURL)</code>: this is a special enhancement to allow users to have telegram \
buttons in their markdown. <code>buttontext</code> will be what is displayed on the button, and <code>someurl</code> \
will be the url which is opened.
EG: <code>[This is a button](buttonurl:example.com)</code>

If you want multiple buttons on the same line, use :same, as such:
<code>[one](buttonurl://example.com)
[two](buttonurl://google.com:same)</code>
This will create two buttons on a single line, instead of one button per line.

Keep in mind that your message <b>MUST</b> contain some text other than just a button!
"""



def get_id(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    chat = update.effective_chat
    msg = update.effective_message
    user_id = extract_user(msg, args)

    if user_id:

        if msg.reply_to_message and msg.reply_to_message.forward_from:

            user1 = message.reply_to_message.from_user
            user2 = message.reply_to_message.forward_from

            msg.reply_text(
                f"<b>Telegram ID:</b>,"
                f"• {html.escape(user2.first_name)} - <code>{user2.id}</code>.\n"
                f"• {html.escape(user1.first_name)} - <code>{user1.id}</code>.",
                parse_mode=ParseMode.HTML)

        else:

            user = bot.get_chat(user_id)
            msg.reply_text(
                f"{html.escape(user.first_name)}'s id is <code>{user.id}</code>.",
                parse_mode=ParseMode.HTML)

    else:

        if chat.type == "private":
            msg.reply_text(
                f"Your id is <code>{chat.id}</code>.",
                parse_mode=ParseMode.HTML)

        else:
            msg.reply_text(
                f"This group's id is <code>{chat.id}</code>.",
                parse_mode=ParseMode.HTML)



def gifid(update: Update, _):
    msg = update.effective_message
    if msg.reply_to_message and msg.reply_to_message.animation:
        update.effective_message.reply_text(
            f"Gif ID:\n<code>{msg.reply_to_message.animation.file_id}</code>",
            parse_mode=ParseMode.HTML)
    else:
        update.effective_message.reply_text(
            "Please reply to a gif to get its ID.")


def info(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    message = update.effective_message
    chat = update.effective_chat
    user_id = extract_user(update.effective_message, args)

    if user_id:
        user = bot.get_chat(user_id)

    elif not message.reply_to_message and not args:
        user = message.from_user

    elif not message.reply_to_message and (
        not args
        or (
            len(args) >= 1
            and not args[0].startswith("@")
            and not args[0].isdigit()
            and not message.parse_entities([MessageEntity.TEXT_MENTION])
        )
    ):
        message.reply_text("I can't extract a user from this.")
        return

    else:
        return

    text = (
        f"<b>Characteristics:</b>\n"
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
            text += "\n\n<b>This person is banned in Spamwatch!</b>"
            text += f"\nReason: <pre>{spamwtc.reason}</pre>"
            text += "\nAppeal at @SpamWatchSupport"
        else:
            pass
    except:
        pass # don't crash if api is down somehow...
    
    Nation_level_present = False

    num_chats = sql.get_user_num_chats(user.id)
    text += f"\nChat count: <code>{num_chats}</code>"

    try:
        user_member = chat.get_member(user.id)
        if user_member.status == "administrator":
            result = requests.post(
                f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id={chat.id}&user_id={user.id}"
            )
            result = result.json()["result"]
            if "custom_title" in result.keys():
                custom_title = result["custom_title"]
                text += f"\nThis user holds the title <b>{custom_title}</b> here."
    except BadRequest:
        pass

    if user.id == OWNER_ID:
            text += f'\nThis person is my owner'
            Nation_level_present = True
    elif user.id in DEV_USERS:
            text += f'\nThis Person is a part of Eagle Union'
            Nation_level_present = True
    elif user.id in SUDO_USERS:
            text += f'\nThe Nation level of this person is Royal'
            Nation_level_present = True
    elif user.id in SUPPORT_USERS:
            text += f'\nThe Nation level of this person is Sakura'
            Nation_level_present = True
    elif user.id in SARDEGNA_USERS:
            text += f'\nThe Nation level of this person is Sardegna'
            Nation_level_present = True
    elif user.id in WHITELIST_USERS:
            text += f'\nThe Nation level of this person is Neptunia'
            Nation_level_present = True
            
    if Nation_level_present:
        text += ' [<a href="https://t.me/{}?start=nations">?</a>]'.format(
            bot.username)

    text += "\n"
    for mod in USER_INFO:
        if mod.__mod_name__ == "Users":
            continue

        try:
            mod_info = mod.__user_info__(user.id)
        except TypeError:
            mod_info = mod.__user_info__(user.id, chat.id)
        if mod_info:
            text += "\n" + mod_info
            
    if INFOPIC:
        try:
            profile = bot.get_user_profile_photos(user.id).photos[0][-1]
            _file = bot.get_file(profile["file_id"])
            _file.download(f"{user.id}.png")

            message.reply_document(
                document=open(f"{user.id}.png", "rb"),
                caption=(text),
                parse_mode=ParseMode.HTML)

            os.remove(f"{user.id}.png")
        # Incase user don't have profile pic, send normal text
        except IndexError:
            message.reply_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    else:
        message.reply_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)





@user_admin
def echo(update: Update, _):
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message

    if message.reply_to_message:
        message.reply_to_message.reply_text(args[1])
    else:
        message.reply_text(args[1], quote=False)

    message.delete()

    
def shell(command):
    process = Popen(command, stdout=PIPE, shell=True, stderr=PIPE)
    stdout, stderr = process.communicate()
    return (stdout, stderr)

@sudo_plus
def ram(update: Update, _):
    cmd = "ps -o pid"
    output = shell(cmd)[0].decode()
    processes = output.splitlines()
    mem = 0
    for p in processes[1:]:
        mem += int(
            float(
                shell(
                    "ps u -p {} | awk ".format(p)
                    + "'{sum=sum+$6}; END {print sum/1024}'"
                )[0]
                .decode()
                .rstrip()
                .replace("'", "")
            )
        )
    update.message.reply_text(
        f"RAM usage = <code>{mem} MiB</code>", parse_mode=ParseMode.HTML
    )




def markdown_help(update: Update, _):
    update.effective_message.reply_text(
        MARKDOWN_HELP, parse_mode=ParseMode.HTML)
    update.effective_message.reply_text(
        "Try forwarding the following message to me, and you'll see!")
    update.effective_message.reply_text(
        "/save test This is a markdown test. _italics_, *bold*, `code`, "
        "[URL](example.com) [button](buttonurl:github.com) "
        "[button2](buttonurl://google.com:same)")



@sudo_plus
def stats(update: Update, _):
    stats = "Current stats:\n" + "\n".join([mod.__stats__() for mod in STATS])
    result = re.sub(r"(\d+)", r"<code>\1</code>", stats)
    update.effective_message.reply_text(result, parse_mode=ParseMode.HTML)
    
    

def ping(update: Update, _):
    msg = update.effective_message
    start_time = time.time()
    message = msg.reply_text("Pinging...")
    end_time = time.time()
    ping_time = round((end_time - start_time) * 1000, 3)
    message.edit_text("*Pong!!!*\n`{}ms`".format(ping_time),
                    parse_mode=ParseMode.MARKDOWN)


__help__ = """
 - /id: get the current group id. If used by replying to a message, gets that user's id.
 - /gifid: reply to a gif to me to tell you its file ID.
 - /info: get information about a user.
 - /markdownhelp: quick summary of how markdown works in telegram - can only be called in private chats.
 - /ud <word>: Type the word or expression you want to search use.
 - /urban <word>: Same as /ud
 - /paste - Do a paste at `neko.bin`
 - /react: Reacts with a random reaction
 - /weebify <text>: returns a weebified text
 - /tr (language code) as reply to a long message.
 - /time <query> : Gives information about a timezone.
 - /cash : currency converter
   example syntax: /cash 1 USD INR
 - /whois : get info about a user (uses @Pyrogram methods)
 - /spbinfo : get info about a user from @Intellivoid's SpamProtection API
───────────────────────────────
*Last.FM*
Share what you're what listening to with the help of this module!
*Available commands:*
 - /setuser <username>: sets your last.fm username.
 - /clearuser: removes your last.fm username from the bot's database.
 - /lastfm: returns what you're scrobbling on last.fm.
───────────────────────────────
*Math*
Solves complex math problems using https://newton.now.sh
 - /math: Simplify `/simplify 2^2+2(2)`
 - /factor: Factor `/factor x^2 + 2x`
 - /derive: Derive `/derive x^2+2x`
 - /integrate: Integrate `/integrate x^2+2x`
 - /zeroes: Find 0's `/zeroes x^2+2x`
 - /tangent: Find Tangent `/tangent 2lx^3`
 - /area: Area Under Curve `/area 2:4lx^3`
 - /cos: Cosine `/cos pi`
 - /sin: Sine `/sin 0`
 - /tan: Tangent `/tan 0`
 - /arccos: Inverse Cosine `/arccos 1`
 - /arcsin: Inverse Sine `/arcsin 0`
 - /arctan: Inverse Tangent `/arctan 0`
 - /abs: Absolute Value `/abs -1`
 - /log: Logarithm `/log 2l8`

__Keep in mind__: To find the tangent line of a function at a certain x value, send the request as c|f(x) where c is the given x value and f(x) is the function expression, the separator is a vertical bar '|'. See the table above for an example request.
To find the area under a function, send the request as c:d|f(x) where c is the starting x value, d is the ending x value, and f(x) is the function under which you want the curve between the two x values.
To compute fractions, enter expressions as numerator(over)denominator. For example, to process 2/4 you must send in your expression as 2(over)4. The result expression will be in standard math notation (1/2, 3/4).

"""

ID_HANDLER = DisableAbleCommandHandler("id", get_id, pass_args=True, run_async=True)
GIFID_HANDLER = DisableAbleCommandHandler("gifid", gifid, run_async=True)
INFO_HANDLER = DisableAbleCommandHandler("info", info, pass_args=True, run_async=True)
ECHO_HANDLER = DisableAbleCommandHandler("echo", echo, filters=Filters.group, run_async=True)
MD_HELP_HANDLER = CommandHandler("markdownhelp", markdown_help, filters=Filters.private, run_async=True)
STATS_HANDLER = CommandHandler("stats", stats, run_async=True)
PING_HANDLER = DisableAbleCommandHandler("ping", ping, run_async=True)
RAM_HANDLER = CommandHandler("ram", ram, run_async=True)
dispatcher.add_handler(ID_HANDLER)
dispatcher.add_handler(GIFID_HANDLER)
dispatcher.add_handler(INFO_HANDLER)
dispatcher.add_handler(ECHO_HANDLER)
dispatcher.add_handler(MD_HELP_HANDLER)
dispatcher.add_handler(STATS_HANDLER)
dispatcher.add_handler(PING_HANDLER)
dispatcher.add_handler(RAM_HANDLER)

__mod_name__ = "Misc"
__command_list__ = ["id", "info", "echo", "ping"]
__handlers__ = [
    ID_HANDLER,
    GIFID_HANDLER,
    INFO_HANDLER,
    ECHO_HANDLER,
    MD_HELP_HANDLER,
    STATS_HANDLER,
    PING_HANDLER,
]
