from tg_bot import (
    OWNER_ID,
    dispatcher,
    log,
    CF_API_KEY
)
from tg_bot.modules.connection import connected
import requests
from tg_bot.modules.global_bans import SPB_MODE
from tg_bot.modules.helper_funcs.chat_status import (
    is_user_admin,
    support_plus,
    user_admin,
)
from telegram.ext import CallbackContext, CommandHandler, Filters, MessageHandler
import tg_bot.modules.sql.nlp_detect_sql as sql
from telegram.error import BadRequest
from telegram import ParseMode, Update

@user_admin
def nlpstat(update: Update, context: CallbackContext):
    args = context.args
    if len(args) > 0:
        if args[0].lower() in ["on", "yes"]:
            sql.enable_nlp_bans(update.effective_chat.id)
            update.effective_message.reply_text(
                "I've enabled NLP in this group. This will help protect you "
                "from spammers, unsavoury characters, and the biggest trolls."
            )
        elif args[0].lower() in ["off", "no"]:
            sql.disable_nlp_bans(update.effective_chat.id)
            update.effective_message.reply_text(
                "I've disabled NLP in this group. The AI based bans wont affect your users "
                "anymore. You'll be less protected from any trolls and spammers "
                "though!"
            )
    else:
        update.effective_message.reply_text(
            "Give me some arguments to choose a setting! on/off, yes/no!\n\n"
            "Your current setting is: {}\n"
            "When True, @Intellivoid's coffehouse AI will keep track of Spammers. "
            "When False, they won't, leaving you at the possible mercy of "
            "spammers.".format(sql.does_chat_nlp_ban(update.effective_chat.id))
        )

@user_admin
def set_nlp_action(update, context):
    args = context.args
    chat_id = update.effective_chat.id
    
    if args[0].lower() == "ban":
        settypeaction = "ban"
        sql.set_action(chat_id, 1, "0")
        update.effective_message.reply_text("NLP mode set to ban")
    elif args[0].lower() == "notify":
        settypeaction = "notify"
        sql.set_action(chat_id, 2, "0")
        update.effective_message.reply_text("NLP mode set to notify")
    else:
        update.effective_message.reply_text("I only understand ban/notify!"
        )



def check_and_ban(update, user_id, should_message=True):

    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message.text
    getmode, getvalue = sql.get_nlp_mode(chat.id)
    if SPB_MODE and CF_API_KEY:
        try:
            result = requests.get(f'https://api.intellivoid.net/coffeehouse/v1/nlp/spam_prediction/chatroom?input={msg}',params={'access_key' : CF_API_KEY})
            res_json = result.json()
            if res_json['success']:
                spam_check = res_json['results']['spam_prediction']['is_spam']
                if spam_check == True and getmode == 1:
                    pred = res_json['results']['spam_prediction']['prediction']
                    update.effective_chat.kick_member(user_id)
                    if should_message:
                        try:
                            update.effective_message.reply_text(
                            f"*⚠ SPAM DETECTED!*\nSpam Prediction: {pred}\nUser: `{user_id}` was banned.",
                            parse_mode=ParseMode.MARKDOWN,
                        )
                        except BadRequest:
                            update.effective_message.reply_text(
                            f"*⚠ SPAM DETECTED!*\nSpam Prediction: {pred}\nUser: `{user_id}`\nUser could not be banned due to insufficient admin perms.",
                            parse_mode=ParseMode.MARKDOWN,
                        )
                if spam_check == True and getmode == 2:
                    pred = res_json['results']['spam_prediction']['prediction']
                    if should_message:
                            update.effective_message.reply_text(
                            f"*⚠ SPAM DETECTED!*\nSpam Prediction: {pred}\nUser: `{user_id}`\nUser could not be banned due to current chat settings.",
                            parse_mode=ParseMode.MARKDOWN,
                        )

            elif res_json['error']['error_code'] == 21:
                reduced_msg = msg[0:170]
                result = requests.get(f'https://api.intellivoid.net/coffeehouse/v1/nlp/spam_prediction/chatroom?input={reduced_msg}',params={'access_key' : CF_API_KEY})
                res_json = result.json()
                if spam_check == True and getmode == 1:
                    spam_check = res_json['results']['spam_prediction']['is_spam']
                    if spam_check:
                        pred = res_json['results']['spam_prediction']['prediction']
                        update.effective_chat.kick_member(user_id)
                        if should_message:
                            try:
                                update.effective_message.reply_text(
                                f"*⚠ SPAM DETECTED!*\nSpam Prediction: {pred}\nUser: `{user_id}` was banned.",
                                parse_mode=ParseMode.MARKDOWN,
                            )
                            except BadRequest:
                                update.effective_message.reply_text(
                                f"*⚠ SPAM DETECTED!*\nSpam Prediction: {pred}\nUser: `{user_id}`\nUser could not be banned due to insufficient admin perms.",
                                parse_mode=ParseMode.MARKDOWN,
                            )
                if spam_check == True and getmode == 2:
                    pred = res_json['results']['spam_prediction']['prediction']
                    if should_message:
                            update.effective_message.reply_text(
                            f"*⚠ SPAM DETECTED!*\nSpam Prediction: {pred}\nUser: `{user_id}`\nUser could not be banned due to current chat settings.",
                            parse_mode=ParseMode.MARKDOWN,
                        )

        except ConnectionError:
            log.warning("Spam Protection API is unreachable.")



def nlp_action(update: Update, context: CallbackContext):
    # Not using @restrict handler to avoid spamming - just ignore if cant gban.
    bot = context.bot
    if (
        sql.does_chat_nlp_ban(update.effective_chat.id)
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

NLP_ACTION_STATUS = CommandHandler(
    "nlpstat", nlpstat, filters=Filters.chat_type.groups, run_async=True
)

NLP_BAN_ENFORCER = MessageHandler(
    Filters.all & Filters.chat_type.groups, nlp_action, run_async=True
)

SET_NLP_MODE_HANDLER = CommandHandler("nlpmode", set_nlp_action, pass_args=True, filters=Filters.chat_type.groups, run_async=True,
)

dispatcher.add_handler(NLP_ACTION_STATUS)
dispatcher.add_handler(NLP_BAN_ENFORCER)
dispatcher.add_handler(SET_NLP_MODE_HANDLER)
