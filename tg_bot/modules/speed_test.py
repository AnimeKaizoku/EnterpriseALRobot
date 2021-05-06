import speedtest
from tg_bot import DEV_USERS, dispatcher
from tg_bot.modules.helper_funcs.chat_status import dev_plus
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.ext import CallbackContext
from tg_bot.modules.helper_funcs.decorators import kigcmd, kigcallback


def convert(speed):
    return round(int(speed) / 1048576, 2)


@dev_plus
@kigcmd(command='speedtest')
def speedtestxyz(update: Update, context: CallbackContext):
    buttons = [
        [
            InlineKeyboardButton("Image", callback_data="speedtest_image"),
            InlineKeyboardButton("Text", callback_data="speedtest_text"),
        ]
    ]
    update.effective_message.reply_text(
        "Select SpeedTest Mode", reply_markup=InlineKeyboardMarkup(buttons)
    )


@kigcallback(pattern="speedtest_.*")
def speedtestxyz_callback(update: Update, context: CallbackContext):
    query = update.callback_query

    if query.from_user.id in DEV_USERS:
        msg = update.effective_message.edit_text("Running a speedtest....")
        speed = speedtest.Speedtest()
        speed.get_best_server()
        speed.download()
        speed.upload()
        replymsg = "SpeedTest Results:"

        if query.data == "speedtest_image":
            speedtest_image = speed.results.share()
            update.effective_message.reply_photo(
                photo=speedtest_image, caption=replymsg
            )
            msg.delete()

        elif query.data == "speedtest_text":
            result = speed.results.dict()
            replymsg += f"\nDownload: `{convert(result['download'])}Mb/s`\nUpload: `{convert(result['upload'])}Mb/s`\nPing: `{result['ping']}`"
            update.effective_message.edit_text(replymsg, parse_mode=ParseMode.MARKDOWN)
    else:
        query.answer("You are not a part of Eagle Union.")


__mod_name__ = "SpeedTest"
