import logging
import os
import sys
import time
import spamwatch
import telegram.ext as tg
from telethon import TelegramClient
from pyrogram import Client, errors
from pyrogram.errors.exceptions.bad_request_400 import PeerIdInvalid, ChannelInvalid
from pyrogram.types import Chat, User
from configparser import ConfigParser
from loguru import logger
StartTime = time.time()

# enable logging
class InterceptHandler(logging.Handler):
    LEVELS_MAP = {
        logging.CRITICAL: "CRITICAL",
        logging.ERROR: "ERROR",
        logging.WARNING: "WARNING",
        logging.INFO: "INFO",
        logging.DEBUG: "DEBUG"
    }

    def _get_level(self, record):
        return self.LEVELS_MAP.get(record.levelno, record.levelno)

    def emit(self, record):
        logger_opt = logger.opt(depth=6, exception=record.exc_info, ansi=True, lazy=True)
        logger_opt.log(self._get_level(record), record.getMessage())


logging.basicConfig(handlers=[InterceptHandler()], level=logging.INFO)
log = logging.getLogger(__name__)

BANNER = r"""
    __ __ _                 ______     __                                ____        __
   / //_/(_)___ ___  ______/_  __/__  / /__  ____ __________ _____ ___  / __ )____  / /_             Buit with <3, In Python 3.8.
  / ,<  / / __ `/ / / / __ \/ / / _ \/ / _ \/ __ `/ ___/ __ `/ __ `__ \/ __  / __ \/ __/             Originaly a work of Paul Larsen.
 / /| |/ / /_/ / /_/ / /_/ / / /  __/ /  __/ /_/ / /  / /_/ / / / / / / /_/ / /_/ / /_               
/_/ |_/_/\__, /\__, /\____/_/  \___/_/\___/\__, /_/   \__,_/_/ /_/ /_/_____/\____/\__/
        /____//____/                      /____/


"""

log.info("Kigyo is now ON. | An Eagle Union Project. | Licensed under GPLv3.")
log.info(BANNER)
log.info("Not affiliated to Azur Lane or Yostar in any way whatsoever.")
log.info("Project maintained by: github.com/Dank-del (t.me/dank_as_fuck)")
# if version < 3.6, stop bot.
if sys.version_info[0] < 3 or sys.version_info[1] < 6:
    log.error(
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
WEBHOOK = kigconfig.getboolean("WEBHOOK")
URL = kigconfig.get("URL")
CERT_PATH = kigconfig.get("CERT_PATH")
PORT = kigconfig.getint("PORT")
INFOPIC = kigconfig.getboolean("INFOPIC")
DEL_CMDS = kigconfig.getboolean("DEL_CMDS")
STRICT_GBAN = kigconfig.getboolean("STRICT_GBAN")
ALLOW_EXCL = kigconfig.getboolean("ALLOW_EXCL")
CUSTOM_CMD = kigconfig.get("CUSTOM_CMD")
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
    log.warning("SpamWatch API key is missing! Check your config.ini")
else:
    try:
        sw = spamwatch.Client(spamwatch_api)
    except:
        sw = None
        log.warning("Can't connect to SpamWatch!")

updater = tg.Updater(TOKEN, workers=WORKERS)
telethn = TelegramClient("kigyo", APP_ID, API_HASH)
dispatcher = updater.dispatcher

kp = Client("KigyoPyro", api_id=APP_ID, api_hash=API_HASH, bot_token=TOKEN)
apps = [kp]


async def get_entity(client, entity):
    entity_client = client
    if not isinstance(entity, Chat):
        try:
            entity = int(entity)
        except ValueError:
            pass
        except TypeError:
            entity = entity.id
        try:
            entity = await client.get_chat(entity)
        except (PeerIdInvalid, ChannelInvalid):
            for kp in apps:
                if kp != client:
                    try:
                        entity = await kp.get_chat(entity)
                    except (PeerIdInvalid, ChannelInvalid):
                        pass
                    else:
                        entity_client = kp
                        break
            else:
                entity = await kp.get_chat(entity)
                entity_client = kp
    return entity, entity_client


SUDO_USERS = list(SUDO_USERS) + list(DEV_USERS)
DEV_USERS = list(DEV_USERS)
WHITELIST_USERS = list(WHITELIST_USERS)
SUPPORT_USERS = list(SUPPORT_USERS)
SARDEGNA_USERS = list(SARDEGNA_USERS)
SPAMMERS = list(SPAMMERS)

# Load at end to ensure all prev variables have been set
from tg_bot.modules.helper_funcs.handlers import CustomCommandHandler

if CUSTOM_CMD and len(CUSTOM_CMD) >= 1:
    tg.CommandHandler = CustomCommandHandler


def spamfilters(text, user_id, chat_id):
    # print("{} | {} | {}".format(text, user_id, chat_id))
    if int(user_id) not in SPAMMERS:
        return False

    print("This user is a spammer!")
    return True
