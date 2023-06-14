import html
import random
import time

from telegram import ChatPermissions, ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext, run_async

import tg_bot.modules.fun_strings as fun_strings
from tg_bot import dispatcher
from tg_bot.modules.disable import DisableAbleCommandHandler
from Ftg_bot.modules.helper_funcs.chat_status import is_user_admin
from tg_bot.modules.helper_funcs.extraction import extract_user



@run_async
def truth(update: Update, context: CallbackContext):
    update.effective_message.reply_text(random.choice(fun_strings.TRUTH_STRINGS))

@run_async
def verdad(update: Update, context: CallbackContext):
    update.effective_message.reply_text(random.choice(fun_strings.TRUTH_STRINGS))

@run_async
def dare(update: Update, context: CallbackContext):
    update.effective_message.reply_text(random.choice(fun_strings.DARE_STRINGS))

@run_async
def reto(update: Update, context: CallbackContext):
    update.effective_message.reply_text(random.choice(fun_strings.DARE_STRINGS))




TRUTH_HANDLER = DisableAbleCommandHandler("truth", truth)
VERDAD_HANDLER = DisableAbleCommandHandler("verdad", verdad)
DARE_HANDLER = DisableAbleCommandHandler("dare", dare)
RETO_HANDLER = DisableAbleCommandHandler("reto", reto)

dispatcher.add_handler(TRUTH_HANDLER)
dispatcher.add_handler(VERDAD_HANDLER)
dispatcher.add_handler(DARE_HANDLER)
dispatcher.add_handler(RETO_HANDLER)

__help__ = """
*Vᴇʀᴅᴀᴅ ᴏ Rᴇᴛᴏ*

 ❍ /truth o /verdad *:* Envía una cadena de verdad aleatoria.
 ❍ /dare o /reto *:* Envía una cadena de atrevimiento aleatoria.
"""

__mod_name__ = "Vᴇʀᴅᴀᴅ ᴏ Rᴇᴛᴏ"
