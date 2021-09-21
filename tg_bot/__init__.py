import logging
import os
import sys
import time
import spamwatch
import telegram.ext as tg
from telethon import TelegramClient
from telethon.sessions import MemorySession
from configparser import ConfigParser
from ptbcontrib.postgres_persistence import PostgresPersistence
from logging.config import fileConfig

StartTime = time.time()

def get_user_list(key):
    # Import here to evade a circular import
    from tg_bot.modules.sql import nation_sql
    royals = nation_sql.get_royals(key)
    return [a.user_id for a in royals]

# enable logging

fileConfig('logging.ini')

log = logging.getLogger('[Enterprise]')
logging.getLogger('ptbcontrib.postgres_persistence.postgrespersistence').setLevel(logging.WARNING)
log.info("[ZHONGLI] Zhongli is starting. | An Eagle Union Project. | Licensed under GPLv3.")
log.info("[ZHONGLI] Not affiliated to Azur Lane or Yostar in any way whatsoever.")
log.info("[ZHONGLI] Project maintained by: github.com/LightLegendXR (t.me/LightLegendXR)")

# if version < 3.6, stop bot.
if sys.version_info[0] < 3 or sys.version_info[1] < 7:
    log.error(
        "[ZHONGLI] You MUST have a python version of at least 3.7! Multiple features depend on this. Bot quitting."
    )
    quit(1)

parser = ConfigParser()
parser.read("config.ini")
kigconfig = parser["kigconfig"]

class ZhongliINIT:
    def __init__(self, parser):
        self.parser = parser
        self.SYS_ADMIN = self.parser.getint('SYS_ADMIN', 0)
        self.OWNER_ID = self.parser.getint('OWNER_ID')
        self.OWNER_USERNAME = self.parser.get('OWNER_USERNAME', None)
        self.APP_ID = self.parser.getint("APP_ID")
        self.API_HASH = self.parser.get("API_HASH")
        self.WEBHOOK = self.parser.getboolean('WEBHOOK', False)
        self.URL = self.parser.get('URL', None)
        self.CERT_PATH = self.parser.get('CERT_PATH', None)
        self.PORT = self.parser.getint('PORT', None)
        self.INFOPIC = self.parser.getboolean('INFOPIC', False)
        self.DEL_CMDS = self.parser.getboolean("DEL_CMDS", False)
        self.STRICT_GBAN = self.parser.getboolean("STRICT_GBAN", False)
        self.ALLOW_EXCL = self.parser.getboolean("ALLOW_EXCL", False)
        self.CUSTOM_CMD = ['/', '!']
        self.BAN_STICKER = self.parser.get("BAN_STICKER", None)
        self.TOKEN = self.parser.get("TOKEN")
        self.DB_URI = self.parser.get("SQLALCHEMY_DATABASE_URI")
        self.LOAD = self.parser.get("LOAD").split()
        self.LOAD = list(map(str, self.LOAD))
        self.MESSAGE_DUMP = self.parser.getint('MESSAGE_DUMP', None)
        self.GBAN_LOGS = self.parser.getint('GBAN_LOGS', None)
        self.NO_LOAD = self.parser.get("NO_LOAD").split()
        self.NO_LOAD = list(map(str, self.NO_LOAD))
        self.spamwatch_api = self.parser.get('spamwatch_api', None)
        self.CASH_API_KEY = self.parser.get('CASH_API_KEY', None)
        self.TIME_API_KEY = self.parser.get('TIME_API_KEY', None)
        self.WALL_API = self.parser.get('WALL_API', None)
        self.LASTFM_API_KEY = self.parser.get('LASTFM_API_KEY', None)
        self.CF_API_KEY =  self.parser.get("CF_API_KEY", None)
        self.bot_id = 0 #placeholder
        self.bot_name = "Zhongli" #placeholder
        self.bot_username = "Zhongli567bot" #placeholder


    def init_sw(self):
        if self.spamwatch_api is None:
            log.warning("SpamWatch API key is missing! Check your config.ini")
            return None
        else:
            try:
                sw = spamwatch.Client(spamwatch_api)
                return sw
            except:
                sw = None
                log.warning("Can't connect to SpamWatch!")
                return sw


KInit = ZhongliINIT(parser=kigconfig)

SYS_ADMIN = KInit.SYS_ADMIN
OWNER_ID = KInit.OWNER_ID
OWNER_USERNAME = KInit.OWNER_USERNAME
APP_ID = KInit.APP_ID
API_HASH = KInit.API_HASH
WEBHOOK = KInit.WEBHOOK
URL = KInit.URL
CERT_PATH = KInit.CERT_PATH
PORT = KInit.PORT
INFOPIC = KInit.INFOPIC
DEL_CMDS = KInit.DEL_CMDS
ALLOW_EXCL = KInit.ALLOW_EXCL
CUSTOM_CMD = KInit.CUSTOM_CMD
BAN_STICKER = KInit.BAN_STICKER
TOKEN = KInit.TOKEN
DB_URI = KInit.DB_URI
LOAD = KInit.LOAD
MESSAGE_DUMP = KInit.MESSAGE_DUMP
GBAN_LOGS = KInit.GBAN_LOGS
NO_LOAD = KInit.NO_LOAD
SUDO_USERS = [OWNER_ID] + get_user_list("sudos")
DEV_USERS = [OWNER_ID] + get_user_list("devs")
SUPPORT_USERS = get_user_list("supports")
SARDEGNA_USERS = get_user_list("sardegnas")
WHITELIST_USERS = get_user_list("whitelists")
SPAMMERS = get_user_list("spammers")
spamwatch_api = KInit.spamwatch_api
CASH_API_KEY = KInit.CASH_API_KEY
TIME_API_KEY = KInit.TIME_API_KEY
WALL_API = KInit.WALL_API
LASTFM_API_KEY = KInit.LASTFM_API_KEY
CF_API_KEY = KInit.CF_API_KEY

SPB_MODE = kigconfig.getboolean('SPB_MODE', False)

# SpamWatch
sw = KInit.init_sw()

from tg_bot.modules.sql import SESSION


updater = tg.Updater(TOKEN, workers=min(32, os.cpu_count() + 4), request_kwargs={"read_timeout": 10, "connect_timeout": 10}, persistence=PostgresPersistence(SESSION))
telethn = TelegramClient(MemorySession(), APP_ID, API_HASH)
dispatcher = updater.dispatcher



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
