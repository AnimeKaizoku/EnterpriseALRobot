from tg_bot import log
import tg_bot.modules.sql.nlp_detect_sql as sql
from tg_bot.modules.language import gs
from tg_bot.modules.helper_funcs.decorators import kigcmd, kigmsg
import requests, telegram
from tg_bot.modules.helper_funcs.chat_status import (
    bot_admin,
    user_admin,
)

__mod_name__ = "NLP"

def get_help(chat):
    return gs(chat, "nlp_help")


@kigcmd(command="nlpstat", group=8)
@user_admin
@bot_admin
def nlp_mode(update, context):
    message = update.effective_message
    args = context.args

    if len(args) > 1:
        if args[1].lower() in ["on", "yes"]:
            sql.enable_nlp(message.chat.id)
            message.reply_text(
                    "I've enabled NLP moderation in this group. This will help protect you "
                    "from spammers, unsavoury characters, and the biggest trolls."
                )
        elif args[1].lower() in ["off", "no"]:
            sql.disable_nlp(message.chat.id)
            message.reply_text(
                    "I've disabled NLP moderation in this group. NLP wont affect your users "
                    "anymore. You'll be less protected from any trolls and spammers "
                    "though!"
                )
    else:
        message.reply_text(
                "Give me some arguments to choose a setting! on/off, yes/no!\n\n"
                "Your current setting is: {}\n"
                "When True, any messsages will go through NLP and spammers will be banned.\n"
                "When False, they won't, leaving you at the possible mercy of spammers\n"
                "NLP powered by @Intellivoid.".format(sql.does_chat_nlp(message.chat.id))
            )


@kigmsg(group=3)
def detect_spam(update, context):  # sourcery no-metrics
    user = update.effective_user
    chat = update.effective_chat
    msg = update.effective_message
    bot = context.bot
    if user.id == bot.id:
        return

    from tg_bot import SPB_MODE, CF_API_KEY
    chat_state = sql.does_chat_nlp(chat.id)
    if SPB_MODE and CF_API_KEY and chat_state == True:
        url = "https://api.intellivoid.net/coffeehouse/v1/nlp/spam_prediction/chatroom"
        try:
            payload = {'access_key': CF_API_KEY, 'input': msg}
            data = requests.post(url, data=payload)
            res_json = data.json()
            if res_json['success']:
                spam_check = res_json['results']['spam_prediction']['is_spam']
                if spam_check == True:
                    pred = res_json['results']['spam_prediction']['prediction']
                    try:
                        bot.restrict_chat_member(chat.id, user.id, telegram.ChatPermissions(can_send_messages=False))
                        msg.reply_text(
                        f"*⚠ SPAM DETECTED!*\nSpam Prediction: `{pred}`\nUser: `{telegram.utils.helpers.mention_markdown(user.id)}` was muted.",
                        parse_mode=telegram.ParseMode.MARKDOWN,
                    )
                    except telegram.BadRequest:
                        msg.reply_text(
                        f"*⚠ SPAM DETECTED!*\nSpam Prediction: `{pred}`\nUser: `{telegram.utils.helpers.mention_markdown(user.id)}`\nUser could not be restricted due to insufficient admin perms.",
                        parse_mode=telegram.ParseMode.MARKDOWN,
                    )

            elif res_json['error']['error_code'] == 21:
                reduced_msg = msg[0:170]
                payload = {'access_key': CF_API_KEY, 'input': reduced_msg}
                data = requests.post(url, data=payload)
                res_json = data.json()
                spam_check = res_json['results']['spam_prediction']['is_spam']
                if spam_check is True:
                    pred = res_json['results']['spam_prediction']['prediction']
                    try:
                        bot.restrict_chat_member(chat.id, user.id, telegram.ChatPermissions(can_send_messages=False))
                        msg.reply_text(
                            f"*⚠ SPAM DETECTED!*\nSpam Prediction: `{pred}`\nUser: `{telegram.utils.helpers.mention_markdown(user.id)}` was muted.", parse_mode=telegram.ParseMode.MARKDOWN)
                    except telegram.BadRequest:
                        msg.reply_text(f"*⚠ SPAM DETECTED!*\nSpam Prediction: `{pred}`\nUser: `{telegram.utils.helpers.mention_markdown(user.id)}`\nUser could not be restricted due to insufficient admin perms.", parse_mode=telegram.ParseMode.MARKDOWN)
        except BaseException as e:
            log.warning(f"Can't reach SpamProtection API due to {e}")
            return
