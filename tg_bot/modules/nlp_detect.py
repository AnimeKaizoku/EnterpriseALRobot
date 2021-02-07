from pyrogram import filters
from tg_bot import kp, CF_API_KEY, log
from pyrogram.handlers import MessageHandler
from pyrogram.types import ChatPermissions
from pyrogram.errors import BadRequest
import requests
from tg_bot.modules.global_bans import SPB_MODE


@kp.on_message(filters.text & filters.group, group=3)
async def detect_spam(client, message):
    user = message.from_user
    chat = message.chat
    if SPB_MODE and CF_API_KEY:
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