import logging
import os
import sys
import time
import spamwatch
import telegram.ext as tg
from telethon import TelegramClient
from pyrogram import Client, errors
from googletrans import Translator
from configparser import ConfigParser

StartTime = time.time()

# enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

LOGGER = logging.getLogger(__name__)
LOGGER.info("Kigyo is now ON. | An Eagle Union Project. | Licensed under GPLv3.")
LOGGER.info(" _   __                           ")
LOGGER.info("| | / / (_)    __    _   _     __  ")
LOGGER.info("|    \  | |  / _` | | | | |  / _ \  ")
LOGGER.info("| |\  \ | | | (_| | | |_| | | (_) |  ")
LOGGER.info("\_| \_/ |_|  \__, |  \__, |  \___/  ")
LOGGER.info("              __/ |   __/ |       ")
LOGGER.info("             |___/   |___/       ")
LOGGER.info("                                   ")
LOGGER.info("By github.com/Dank-del (t.me/dank_as_fuck)")
# if version < 3.6, stop bot.
if sys.version_info[0] < 3 or sys.version_info[1] < 6:
    LOGGER.error(
        "You MUST have a python version of at least 3.6! Multiple features depend on this. Bot quitting."
    )
    quit(1)

parser = ConfigParser()
parser.read("config.ini")
kigconfig = parser["kigconfig"]


OWNER_ID = kigconfig.getint("OWNER_ID")
OWNER_USERNAME = kigconfig.get("OWNER_USERNAME")
APP_ID = kigconfig.getint("APP_ID")
API_HASH = kigconfig.get("API_HASH")
DONATION_LINK = kigconfig.get("DONATION_LINK")
WEBHOOK = kigconfig.getboolean("WEBHOOK")
URL = kigconfig.get("URL")
CERT_PATH = kigconfig.get("CERT_PATH")
PORT = kigconfig.getint("PORT")
INFOPIC = kigconfig.getboolean("INFOPIC")
DEL_CMDS = kigconfig.getboolean("DEL_CMDS")
STRICT_GBAN = kigconfig.getboolean("STRICT_GBAN")
ALLOW_EXCL = kigconfig.getboolean("ALLOW_EXCL")
BAN_STICKER = kigconfig.get("BAN_STICKER")
WORKERS = kigconfig.getint("WORKERS")
TOKEN = kigconfig.get("TOKEN")
DB_URI = kigconfig.get("SQLALCHEMY_DATABASE_URI")
LOAD = kigconfig.get("LOAD").split()
LOAD = list(map(str, LOAD))
MESSAGE_DUMP = kigconfig.getfloat("MESSAGE_DUMP")
GBAN_LOGS = kigconfig.getfloat("GBAN_LOGS")
NO_LOAD = kigconfig.get("NO_LOAD").split()
NO_LOAD = list(map(str, NO_LOAD))
SUDO_USERS = kigconfig.get("SUDO_USERS").split()
SUDO_USERS = list(map(int, SUDO_USERS))
DEV_USERS = kigconfig.get("DEV_USERS").split()
DEV_USERS = list(map(int, DEV_USERS))
SUPPORT_USERS = kigconfig.get("SUPPORT_USERS").split()
SUPPORT_USERS = list(map(int, SUPPORT_USERS))
SARDEGNA_USERS = kigconfig.get("SARDEGNA_USERS").split()
SARDEGNA_USERS = list(map(int, SARDEGNA_USERS))
WHITELIST_USERS = kigconfig.get("WHITELIST_USERS").split()
WHITELIST_USERS = list(map(int, WHITELIST_USERS))
SPAMMERS = kigconfig.get("SPAMMERS").split()
SPAMMERS = list(map(int, SPAMMERS))
spamwatch_api = kigconfig.get("spamwatch_api")
CASH_API_KEY = kigconfig.get("CASH_API_KEY")
TIME_API_KEY = kigconfig.get("TIME_API_KEY")
WALL_API = kigconfig.get("WALL_API")
LASTFM_API_KEY = kigconfig.get("LASTFM_API_KEY")


SUDO_USERS.append(OWNER_ID)
DEV_USERS.append(OWNER_ID)

# SpamWatch
if spamwatch_api is None:
    sw = None
    LOGGER.warning("SpamWatch API key is missing! Check your config.env.")
else:
    sw = spamwatch.Client(spamwatch_api)


updater = tg.Updater(TOKEN, workers=WORKERS)
telethn = TelegramClient("kigyo", APP_ID, API_HASH)
dispatcher = updater.dispatcher

kp = Client("KigyoPyro", api_id=APP_ID, api_hash=API_HASH, bot_token=TOKEN)

SUDO_USERS = list(SUDO_USERS) + list(DEV_USERS)
DEV_USERS = list(DEV_USERS)
WHITELIST_USERS = list(WHITELIST_USERS)
SUPPORT_USERS = list(SUPPORT_USERS)
SARDEGNA_USERS = list(SARDEGNA_USERS)
SPAMMERS = list(SPAMMERS)

# Load at end to ensure all prev variables have been set
from tg_bot.modules.helper_funcs.handlers import (
    CustomHandler,
    CustomCommandHandler,
    CustomRegexHandler,
    CustomMessageHandler,
)

# make sure the regex handler can take extra kwargs
tg.handler.Handler = CustomHandler
tg.RegexHandler = CustomRegexHandler
tg.CommandHandler = CustomCommandHandler
tg.MessageHandler = CustomMessageHandler


def spamfilters(text, user_id, chat_id):
    # print("{} | {} | {}".format(text, user_id, chat_id))
    if int(user_id) in SPAMMERS:
        print("This user is a spammer!")
        return True
    else:
        return False


# Initialize Translator
trl = Translator()
