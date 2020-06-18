import time
from typing import List

import requests
from telegram import Bot, Update, ParseMode
from telegram.ext import run_async

from tg_bot import dispatcher, StartTime
from tg_bot.modules.disable import DisableAbleCommandHandler

sites_list = {
    "Telegram": "https://api.telegram.org",
    "Kaizoku": "https://animekaizoku.com",
    "Kayo": "https://animekayo.com",
    "Jikan": "https://api.jikan.moe/v3"
}


def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        if count < 3:
            remainder, result = divmod(seconds, 60)
        else:
            remainder, result = divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "

    time_list.reverse()
    ping_time += ":".join(time_list)

    return ping_time


def ping_func(to_ping: List[str]) -> List[str]:
    ping_result = []

    for each_ping in to_ping:

        start_time = time.time()
        site_to_ping = sites_list[each_ping]
        r = requests.get(site_to_ping)
        end_time = time.time()
        ping_time = str(round((end_time - start_time), 2)) + "s"

        pinged_site = f"<b>{each_ping}</b>"

        if each_ping is "Kaizoku" or each_ping is "Kayo":
            pinged_site = f'<a href="{sites_list[each_ping]}">{each_ping}</a>'
            ping_time = f"<code>{ping_time} (Status: {r.status_code})</code>"

        ping_text = f"{pinged_site}: <code>{ping_time}</code>"
        ping_result.append(ping_text)

    return ping_result


@run_async
def ping(bot: Bot, update: Update):
    telegram_ping = ping_func(["Telegram"])[0].split(": ", 1)[1]
    uptime = get_readable_time((time.time() - StartTime))

    reply_msg = ("PONG!!\n"
                 "<b>Time Taken:</b> <code>{}</code>\n"
                 "<b>Service uptime:</b> <code>{}</code>".format(telegram_ping, uptime))

    update.effective_message.reply_text(reply_msg, parse_mode=ParseMode.HTML)


@run_async
def pingall(bot: Bot, update: Update):
    to_ping = ["Kaizoku", "Kayo", "Telegram", "Jikan"]
    pinged_list = ping_func(to_ping)
    pinged_list.insert(2, '')
    uptime = get_readable_time((time.time() - StartTime))

    reply_msg = "⏱Ping results are:\n"
    reply_msg += "\n".join(pinged_list)
    reply_msg += '\n<b>Service uptime:</b> <code>{}</code>'.format(uptime)

    update.effective_message.reply_text(reply_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

PING_HANDLER = DisableAbleCommandHandler("ping", ping)
PINGALL_HANDLER = DisableAbleCommandHandler("pingall", pingall)

dispatcher.add_handler(PING_HANDLER)
dispatcher.add_handler(PINGALL_HANDLER)
__command_list__ = ["ping", "pingall"]
__handlers__ = [PING_HANDLER, PINGALL_HANDLER]
