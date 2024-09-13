import logging
import sys
import time
from typing import List
from redis import Redis
import telegram.ext as tg
from configparser import ConfigParser
from logging.handlers import RotatingFileHandler
from dataclasses import dataclass


StartTime = time.time()


def get_user_list(key):
    from tg_bot.modules.sql import nation_sql

    royals = nation_sql.get_royals(key)
    return [a.user_id for a in royals]


parser = ConfigParser()
parser.read("config.ini")
kigconfig = parser["kigconfig"]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        RotatingFileHandler("kigyo.log", maxBytes=1024 * 1024, backupCount=5),
        logging.StreamHandler(),
    ],
    level=logging.DEBUG if kigconfig.getboolean("IS_DEBUG", False) else logging.WARN,
)

log = logging.getLogger("[Enterprise]")
logging.getLogger("ptbcontrib.postgres_persistence.postgrespersistence").setLevel(
    logging.WARNING
)

log.info("[KIGYO] Kigyo is starting. | An Eagle Union Project. | Licensed under GPLv3.")
log.info("[KIGYO] Not affiliated to Azur Lane or Yostar in any way whatsoever.")
log.info("[KIGYO] Project maintained by: github.com/Dank-del (t.me/dank_as_fuck)")

if sys.version_info < (3, 7):
    log.error(
        "[KIGYO] You MUST have a python version of at least 3.7! Multiple features depend on this. Bot quitting."
    )
    sys.exit(1)


@dataclass
class KigyoINIT:
    def __init__(self, parser: ConfigParser):
        self.parser = parser
        self.SYS_ADMIN: int = self.parser.getint("SYS_ADMIN", 0)
        self.OWNER_ID: int = self.parser.getint("OWNER_ID")
        self.OWNER_USERNAME: str = self.parser.get("OWNER_USERNAME", None)
        self.APP_ID: int = self.parser.getint("APP_ID")
        self.API_HASH: str = self.parser.get("API_HASH")
        self.WEBHOOK: bool = self.parser.getboolean("WEBHOOK", False)
        self.URL: str = self.parser.get("URL", None)
        self.CERT_PATH: str = self.parser.get("CERT_PATH", None)
        self.PORT: int = self.parser.getint("PORT", None)
        self.INFOPIC: bool = self.parser.getboolean("INFOPIC", False)
        self.DEL_CMDS: bool = self.parser.getboolean("DEL_CMDS", False)
        self.STRICT_GBAN: bool = self.parser.getboolean("STRICT_GBAN", False)
        self.ALLOW_EXCL: bool = self.parser.getboolean("ALLOW_EXCL", False)
        self.CUSTOM_CMD: List[str] = ["/", "!"]
        self.BAN_STICKER: str = self.parser.get("BAN_STICKER", None)
        self.TOKEN: str = self.parser.get("TOKEN")
        self.DB_URI: str = self.parser.get("SQLALCHEMY_DATABASE_URI")
        self.LOAD: List[str] = self.parser.get("LOAD", "").split()
        self.MESSAGE_DUMP: int = self.parser.getint("MESSAGE_DUMP", None)
        self.GBAN_LOGS: int = self.parser.getint("GBAN_LOGS", None)
        self.NO_LOAD: List[str] = self.parser.get("NO_LOAD", "").split()
        self.CASH_API_KEY: str = self.parser.get("CASH_API_KEY", None)
        self.TIME_API_KEY: str = self.parser.get("TIME_API_KEY", None)
        self.WALL_API: str = self.parser.get("WALL_API", None)
        self.LASTFM_API_KEY: str = self.parser.get("LASTFM_API_KEY", None)
        self.CF_API_KEY: str = self.parser.get("CF_API_KEY", None)
        self.bot_id: int = 0
        self.bot_name: str = "Kigyo"
        self.bot_username: str = "KigyoRobot"
        self.DEBUG: bool = self.parser.getboolean("IS_DEBUG", False)
        self.DROP_UPDATES: bool = self.parser.getboolean("DROP_UPDATES", True)
        self.BOT_API_URL: str = self.parser.get(
            "BOT_API_URL", "https://api.telegram.org/bot"
        )
        self.BOT_API_FILE_URL: str = self.parser.get(
            "BOT_API_FILE_URL", "https://api.telegram.org/file/bot"
        )
        self.POSTGRES_POOL_SIZE: int = self.parser.getint("POSTGRES_POOL_SIZE", 1)
        self.POSTGRES_MAX_OVERFLOW: int = self.parser.getint(
            "POSTGRES_MAX_OVERFLOW", 10
        )
        self.POSTGRES_POOL_TIMEOUT: int = self.parser.getint(
            "POSTGRES_POOL_TIMEOUT", 30
        )
        self.POSTGRES_POOL_RECYCLE: int = self.parser.getint(
            "POSTGRES_POOL_RECYCLE", 1800
        )
        self.REDIS_HOST: str = self.parser.get("REDIS_HOST", "localhost")
        self.REDIS_PORT: int = self.parser.getint("REDIS_PORT", 6379)
        self.REDIS_DB: int = self.parser.getint("REDIS_DB", 0)
        self.REDIS_PASSWORD: str = self.parser.get("REDIS_PASSWORD", None)


KInit = KigyoINIT(parser=kigconfig)

# Global variables
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
CASH_API_KEY = KInit.CASH_API_KEY
TIME_API_KEY = KInit.TIME_API_KEY
WALL_API = KInit.WALL_API
LASTFM_API_KEY = KInit.LASTFM_API_KEY
CF_API_KEY = KInit.CF_API_KEY
POSTGRES_POOL_SIZE = KInit.POSTGRES_POOL_SIZE
REDIS_HOST = KInit.REDIS_HOST
REDIS_PORT = KInit.REDIS_PORT
REDIS_PASSWORD = KInit.REDIS_PASSWORD
REDIS_DB = KInit.REDIS_DB


# Configure Redis connection
redis_conn = Redis(
    host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=REDIS_DB
)

# Test Redis connection
try:
    redis_conn.ping()
    log.info("Redis connection successful")
except Exception as e:
    log.error(f"Redis connection failed: {e}")

updater = tg.Updater(
    token=TOKEN,
    base_url=KInit.BOT_API_URL,
    base_file_url=KInit.BOT_API_FILE_URL,
    workers=32,
    request_kwargs={"read_timeout": 10, "connect_timeout": 10},
)
dispatcher = updater.dispatcher


# Load at end to ensure all prev variables have been set
from tg_bot.modules.helper_funcs.handlers import CustomCommandHandler

if CUSTOM_CMD and len(CUSTOM_CMD) >= 1:
    tg.CommandHandler = CustomCommandHandler


def spamfilters(text, user_id, chat_id):
    return int(user_id) in SPAMMERS
