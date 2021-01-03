from tg_bot import dispatcher
from tg_bot.modules.disable import DisableAbleCommandHandler
from telegram import Update
from telegram.ext import CallbackContext


def shout(update: Update, context: CallbackContext):
    args = context.args
    text = " ".join(args)
    result = []
    result.append(" ".join(list(text)))
    for pos, symbol in enumerate(text[1:]):
        result.append(symbol + " " + "  " * pos + symbol)
    result = list("\n".join(result))
    result[0] = text[0]
    result = "".join(result)
    msg = "```\n" + result + "```"
    return update.effective_message.reply_text(msg, parse_mode="MARKDOWN")


SHOUT_HANDLER = DisableAbleCommandHandler(
    "shout", shout, pass_args=True, run_async=True
)

dispatcher.add_handler(SHOUT_HANDLER)

__command_list__ = ["shout"]
__handlers__ = [SHOUT_HANDLER]
