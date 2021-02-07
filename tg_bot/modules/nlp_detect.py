from pyrogram import filters
from tg_bot import kp, CF_API_KEY, log
from pyrogram.handlers import MessageHandler
from pyrogram.types import ChatPermissions
from pyrogram.errors import BadRequest
import requests
from tg_bot.modules.global_bans import SPB_MODE
import tg_bot.modules.sql.nlp_detect_sql as sql
from tg_bot.modules.language import gs

__mod_name__ = "NLP"

def get_help(chat):
    return gs(chat, "nlp_help")

@kp.on_message(filters.command("nlpstat"), group=8)
async def nlp_mode(client, message):
    print("ok")
    args = message.text.split(None, 1)
    if len(args) > 1:
        if args[1].lower() in ["on", "yes"]:
            sql.enable_nlp(message.chat.id)
            await message.reply_text(
                "I've enabled NLP moderation in this group. This will help protect you "
                "from spammers, unsavoury characters, and the biggest trolls."
            )
        elif args[1].lower() in ["off", "no"]:
            sql.disable_nlp(message.chat.id)
            await message.reply_text(
                "I've disabled NLP moderation in this group. NLP wont affect your users "
                "anymore. You'll be less protected from any trolls and spammers "
                "though!"
            )
    else:
        await message.reply_text(
            "Give me some arguments to choose a setting! on/off, yes/no!\n\n"
            "Your current setting is: {}\n"
            "When True, any messsages will go through NLP and spammers will be banned. "
            "When False, they won't, leaving you at the possible mercy of spammers "
            "NLP powered by @Intellivoid.".format(sql.does_chat_nlp(message.chat.id))
        )

@kp.on_message(filters.text & filters.group, group=3)
async def detect_spam(client, message):
    user = message.from_user
    chat = message.chat
    chat_state = sql.does_chat_nlp(chat.id)
    if SPB_MODE and CF_API_KEY and chat_state == True:
        try:
            result = requests.get(f'https://api.intellivoid.net/coffeehouse/v1/nlp/spam_prediction/chatroom?input={message.text}',params={'access_key' : CF_API_KEY})
            res_json = result.json()
            if res_json['success']:
                spam_check = res_json['results']['spam_prediction']['is_spam']
                if spam_check == True:
                    pred = res_json['results']['spam_prediction']['prediction']
                    await kp.restrict_chat_member(chat.id, user.id, ChatPermissions(can_send_messages=False))
                    try:
                        await message.reply_text(
                        f"**⚠ SPAM DETECTED!**\nSpam Prediction: `{pred}`\nUser: `{user.id}` was muted.",
                        parse_mode="md",
                    )
                    except BadRequest:
                        await message.reply_text(
                        f"**⚠ SPAM DETECTED!**\nSpam Prediction: `{pred}`\nUser: `{user.id}`\nUser could not be restricted due to insufficient admin perms.",
                        parse_mode="md",
                    )

            elif res_json['error']['error_code'] == 21:
                reduced_msg = message.text[0:170]
                result = requests.get(f'https://api.intellivoid.net/coffeehouse/v1/nlp/spam_prediction/chatroom?input={reduced_msg}',params={'access_key' : CF_API_KEY})
                res_json = result.json()
                spam_check = res_json['results']['spam_prediction']['is_spam']
                if spam_check is True:
                    pred = res_json['results']['spam_prediction']['prediction']
                    await kp.restrict_chat_member(chat.id, user.id, ChatPermissions(can_send_messages=False))
                    try:
                        await message.reply_text(
                            f"**⚠ SPAM DETECTED!**\nSpam Prediction: `{pred}`\nUser: `{user.id}` was muted.", parse_mode="markdown")
                    except BadRequest:
                        await message.reply_text(f"**⚠ SPAM DETECTED!**\nSpam Prediction: `{pred}`\nUser: `{user.id}`\nUser could not be restricted due to insufficient admin perms.", parse_mode="markdown")
        except ConnectionError:
            log.warning("Can't reach SpamProtection API")
