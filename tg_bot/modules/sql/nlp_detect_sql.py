import threading

from sqlalchemy import Column, UnicodeText, Integer, String, Boolean

from tg_bot.modules.sql import BASE, SESSION



class NLPSettings(BASE):
    __tablename__ = "nlp_settings"
    chat_id = Column(String(14), primary_key=True)
    setting = Column(Boolean, default=False, nullable=False)

    def __init__(self, chat_id, disabled):
        self.chat_id = str(chat_id)
        self.setting = disabled

    def __repr__(self):
        return "<NLP setting {} ({})>".format(self.chat_id, self.setting)

class NLPAct(BASE):
    __tablename__ = "nlp_act"
    chat_id = Column(String(14), primary_key=True)
    setting = Column(Boolean, default=False, nullable=False)

    def __init__(self, chat_id, disabled):
        self.chat_id = str(chat_id)
        self.setting = disabled

    def __repr__(self):
        return "<NLP mode {} ({})>".format(self.chat_id, self.setting)


NLPAct.__table__.create(checkfirst=True)
NLPSettings.__table__.create(checkfirst=True)

NLP_SETTING_LOCK = threading.RLock()
NLP_MODE_LOCK = threading.RLock()
NLPSETTING_LIST = set()
NLPMODE_LIST = set()

def enable_nlp_mode(chat_id):
    with NLP_SETTING_LOCK:
        chat = SESSION.query(NLPSettings).get(str(chat_id))
        if not chat:
            chat = NLPSettings(chat_id, True)

        chat.setting = True
        SESSION.add(chat)
        SESSION.commit()
        if str(chat_id) in NLPSETTING_LIST:
            NLPSETTING_LIST.remove(str(chat_id))


def disable_nlp_mode(chat_id):
    with NLP_SETTING_LOCK:
        chat = SESSION.query(NLPSettings).get(str(chat_id))
        if not chat:
            chat = NLPSettings(chat_id, False)

        chat.setting = False
        SESSION.add(chat)
        SESSION.commit()
        NLPSETTING_LIST.add(str(chat_id))

def alert_true(chat_id):
    with NLP_MODE_LOCK:
        chat = SESSION.query(NLPAct).get(str(chat_id))
        if not chat:
            chat = NLPAct(chat_id, True)

        chat.setting = True
        SESSION.add(chat)
        SESSION.commit()
        if str(chat_id) in NLPMODE_LIST:
            NLPMODE_LIST.remove(str(chat_id))


def alert_and_ban(chat_id):
    with NLP_MODE_LOCK:
        chat = SESSION.query(NLPAct).get(str(chat_id))
        if not chat:
            chat = NLPAct(chat_id, False)

        chat.setting = False
        SESSION.add(chat)
        SESSION.commit()
        NLPMODE_LIST.add(str(chat_id))


def does_chat_nlp_ban(chat_id):
    return str(chat_id) not in NLPMODE_LIST

def does_chat_nlp(chat_id):
    return str(chat_id) not in NLPSETTING_LIST

def __load_nlp_stat_list():
    global NLPSETTING_LIST
    try:
        NLPSETTING_LIST = {
            x.chat_id for x in SESSION.query(NLPSettings).all() if not x.setting
        }
    finally:
        SESSION.close()

def __load_nlp_mode_list():
    global NLPMODE_LIST
    try:
        NLPMODE_LIST = {
            x.chat_id for x in SESSION.query(NLPAct).all() if not x.setting
        }
    finally:
        SESSION.close()

def migrate_chat(old_chat_id, new_chat_id):
    with NLP_SETTING_LOCK:
        chat = SESSION.query(NLPSettings).get(str(old_chat_id))
        if chat:
            chat.chat_id = new_chat_id
            SESSION.add(chat)

        SESSION.commit()

def migrate_chat(old_chat_id, new_chat_id):
    with NLP_MODE_LOCK:
        chat = SESSION.query(NLPAct).get(str(old_chat_id))
        if chat:
            chat.chat_id = new_chat_id
            SESSION.add(chat)

        SESSION.commit()


# Create in memory userid to avoid disk access
__load_nlp_stat_list()
__load_nlp_mode_list()
