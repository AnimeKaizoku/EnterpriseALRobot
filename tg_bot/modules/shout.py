from typing import List

from telegram import Update, Bot
from telegram.ext import run_async

from tg_bot import dispatcher
from tg_bot.modules.disable import DisableAbleCommandHandler


@run_async
def shout(bot: Bot, update: Update, args: List[str]):
    text = " ".join(args)
    result = [" ".join([s for s in text])]
    for pos, symbol in enumerate(text[1:]):
        result.append(symbol + " " + "  " * pos + symbol)
    result = list("\n".join(result))
    result[0] = text[0]
    result = "".join(result)
    msg = "```\n" + result + "```"
    return update.effective_message.reply_text(msg, parse_mode="MARKDOWN")


SHOUT_HANDLER = DisableAbleCommandHandler("shout", shout, pass_args=True)

dispatcher.add_handler(SHOUT_HANDLER)

__command_list__ = ["shout"]
__handlers__ = [SHOUT_HANDLER]
