from configparser import ConfigParser
import os, logging, threading
from telegram.error import BadRequest
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.filters import Filters
from telegram.ext.messagehandler import MessageHandler

from ..modules.helper_funcs.chat_status import user_admin
from .. import dispatcher
from telegram.ext import CallbackContext
from telegram import Update
from sqlalchemy import Column, String, Boolean

from ..modules.sql import BASE, SESSION

logging.info("Drag and drop Sibyl System Plugin by Sayan Biswas [github.com/Dank-del // t.me/dank_as_fuck] @Kaizoku")


class SibylSettings(BASE):
    __tablename__ = "chat_sibyl_settings"
    chat_id = Column(String(14), primary_key=True)
    setting = Column(Boolean, default=True, nullable=False)

    def __init__(self, chat_id, disabled):
        self.chat_id = str(chat_id)
        self.setting = disabled

    def __repr__(self):
        return "<Sibyl setting {} ({})>".format(self.chat_id, self.setting)


SibylSettings.__table__.create(checkfirst=True)

SIBYL_SETTING_LOCK = threading.RLock()
SIBYLBAN_LIST = set()


def enable_sibyl(chat_id):
    with SIBYL_SETTING_LOCK:
        chat = SESSION.query(SibylSettings).get(str(chat_id))
        if not chat:
            chat = SibylSettings(chat_id, True)

        chat.setting = True
        SESSION.add(chat)
        SESSION.commit()
        if str(chat_id) in SIBYLBAN_LIST:
            SIBYLBAN_LIST.remove(str(chat_id))


def disable_sibyl(chat_id):
    with SIBYL_SETTING_LOCK:
        chat = SESSION.query(SibylSettings).get(str(chat_id))
        if not chat:
            chat = SibylSettings(chat_id, False)

        chat.setting = False
        SESSION.add(chat)
        SESSION.commit()
        SIBYLBAN_LIST.add(str(chat_id))


def __load_sibylban_list():
    global SIBYLBAN_LIST
    try:
        SIBYLBAN_LIST = {
            x.chat_id for x in SESSION.query(SibylSettings).all() if not x.setting
        }
    finally:
        SESSION.close()


def does_chat_sibylban(chat_id):
    return str(chat_id) not in SIBYLBAN_LIST


if os.getenv("ENV", "False") == "False":
    try:
        p = ConfigParser()
        p.read("config.ini")
        sk = p.get("kigconfig", "SIBYL_KEY")
    except BaseException as e:
        logging.warning("Not loading Sibyl System plugin due to {}".format(e))
        sk = None
elif os.getenv("ENV", "False") == "True":
    sk = os.getenv("SIBYL_KEY")

if sk:
    try:
        from SibylSystem import PsychoPass
        from SibylSystem.exceptions import GeneralException
    except ImportError as e:
        logging.warning('Not loading Sibyl System plugin due to {}'.format(e))
    try:
        client = PsychoPass(sk)
        logging.info("Connection to Sibyl System was successful...")
    except BaseException as e:
        logging.warning("Not loading Sibyl System plugin due to {}".format(e))
        client = None
else:
    client = None

# Create in memory userid to avoid disk access
__load_sibylban_list()


def sibyl_ban(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    if not user:
        return
    bot = context.bot
    if not does_chat_sibylban(chat.id):
        return

    if client:
        try:
            data = client.get_info(user.id)
        except GeneralException:
            return
        except BaseException as e:
            logging.error(e)
            return
        if data.banned:
            try:
                bot.kick_chat_member(chat_id=chat.id, user_id=user.id)
            except BadRequest:
                return
            except BaseException as e:
                logging.error("Failed to ban {} in {} due to {}".format(user.id, chat.id, e))
            txt = '''<b>Dominator locked on</b> {}\n'''.format(user.mention_html())
            txt += "Target was Eliminated with <b>{}</b>\n\n".format(
                "Lethal Eliminator" if not data.is_bot else "Destroy Decomposer")
            txt += "<b>Reason:</b> <code>{}</code>\n".format(data.reason)
            txt += "<b>Ban Flag(s):</b> <code>{}</code>\n".format(", ".join(data.ban_flags))
            txt += "<b>Inspector ID:</b> <code>{}</code>\n".format(data.banned_by)
            txt += "<b>Ban time:</b> <code>{}</code>\n\n".format(data.date)
            txt += "<i>If the enforcement was unjust in any way, kindly report it to @PublicSafetyBureau or disable " \
                   "this feature using /sibylban</i> "
            message.reply_html(text=txt, disable_web_page_preview=True)


@user_admin
def toggle_sibyl(update: Update, _: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    do = does_chat_sibylban(chat.id)
    if not do:
        enable_sibyl(chat.id)
        message.reply_text("Dominator enabled for {}".format(chat.title))
    else:
        disable_sibyl(chat.id)
        message.reply_text("Dominator disabled for {}".format(chat.title))

    return


dispatcher.add_handler(MessageHandler(filters=Filters.chat_type.groups, callback=sibyl_ban), group=101)
dispatcher.add_handler(
    CommandHandler(command="sibylban", callback=toggle_sibyl, run_async=True, filters=Filters.chat_type.groups),
    group=100)
