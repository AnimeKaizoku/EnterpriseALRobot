import logging
import os
import sys, json
import time
import spamwatch
import telegram.ext as tg
from telethon import TelegramClient
from pyrogram import Client, errors
from pyrogram.errors.exceptions.bad_request_400 import PeerIdInvalid, ChannelInvalid
from pyrogram.types import Chat, User
from configparser import ConfigParser
from rich.logging import RichHandler
StartTime = time.time()

def get_user_list(__init__, key):
    with open("{}/tg_bot/{}".format(os.getcwd(), __init__), "r") as json_file:
        return json.load(json_file)[key]

# enable logging
FORMAT = "[Enterprise] %(message)s"
logging.basicConfig(handlers=[RichHandler()], level=logging.INFO, format=FORMAT, datefmt="[%X]")
logging.getLogger("pyrogram").setLevel(logging.WARNING)
log = logging.getLogger("rich")

log.info("[KIGYO] Kigyo is starting. | An Eagle Union Project. | Licensed under GPLv3.")

log.info("[KIGYO] Not affiliated to Azur Lane or Yostar in any way whatsoever.")
log.info("[KIGYO] Project maintained by: github.com/Dank-del (t.me/dank_as_fuck)")

# if version < 3.6, stop bot.
if sys.version_info[0] < 3 or sys.version_info[1] < 7:
    log.error(
        "[KIGYO] You MUST have a python version of at least 3.7! Multiple features depend on this. Bot quitting."
    )
    quit(1)

parser = ConfigParser()
parser.read("config.ini")
kigconfig = parser["kigconfig"]


OWNER_ID = kigconfig.getint("OWNER_ID")
OWNER_USERNAME = kigconfig.get("OWNER_USERNAME")
APP_ID = kigconfig.getint("APP_ID")
API_HASH = kigconfig.get("API_HASH")
WEBHOOK = kigconfig.getboolean("WEBHOOK", False)
URL = kigconfig.get("URL", None)
CERT_PATH = kigconfig.get("CERT_PATH", None)
PORT = kigconfig.getint("PORT", None)
INFOPIC = kigconfig.getboolean("INFOPIC", False)
DEL_CMDS = kigconfig.getboolean("DEL_CMDS", False)
STRICT_GBAN = kigconfig.getboolean("STRICT_GBAN", False)
ALLOW_EXCL = kigconfig.getboolean("ALLOW_EXCL", False)
CUSTOM_CMD = kigconfig.get("CUSTOM_CMD", None)
BAN_STICKER = kigconfig.get("BAN_STICKER", None)
TOKEN = kigconfig.get("TOKEN")
DB_URI = kigconfig.get("SQLALCHEMY_DATABASE_URI")
LOAD = kigconfig.get("LOAD").split()
LOAD = list(map(str, LOAD))
MESSAGE_DUMP = kigconfig.getfloat("MESSAGE_DUMP")
GBAN_LOGS = kigconfig.getfloat("GBAN_LOGS")
NO_LOAD = kigconfig.get("NO_LOAD").split()
NO_LOAD = list(map(str, NO_LOAD))
SUDO_USERS = get_user_list("elevated_users.json", "sudos")
DEV_USERS = get_user_list("elevated_users.json", "devs")
SUPPORT_USERS = get_user_list("elevated_users.json", "supports")
SARDEGNA_USERS = get_user_list("elevated_users.json", "sardegnas")
WHITELIST_USERS = get_user_list("elevated_users.json", "whitelists")
SPAMMERS = get_user_list("elevated_users.json", "spammers")
spamwatch_api = kigconfig.get("spamwatch_api")
CASH_API_KEY = kigconfig.get("CASH_API_KEY")
TIME_API_KEY = kigconfig.get("TIME_API_KEY")
WALL_API = kigconfig.get("WALL_API")
LASTFM_API_KEY = kigconfig.get("LASTFM_API_KEY")
try:
    CF_API_KEY = kigconfig.get("CF_API_KEY")
    log.info("[NLP] AI antispam powered by Intellivoid.")
except:
    log.info("[NLP] No Coffeehouse API key provided.")
    CF_API_KEY = None


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

updater = tg.Updater(TOKEN, workers=min(32, os.cpu_count() + 4), request_kwargs={"read_timeout": 10, "connect_timeout": 10})
telethn = TelegramClient("kigyo", APP_ID, API_HASH)
dispatcher = updater.dispatcher

kp = Client("KigyoPyro", api_id=APP_ID, api_hash=API_HASH, bot_token=TOKEN, workers=min(32, os.cpu_count() + 4))
apps = []
apps.append(kp)


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
    if int(user_id) in SPAMMERS:
        print("This user is a spammer!")
        return True
    else:
        return False
