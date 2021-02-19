import threading

from sqlalchemy import Column, UnicodeText, Integer, String, Boolean

from tg_bot.modules.sql import BASE, SESSION




class NLPSettings(BASE):
    __tablename__ = "chat_nlp_settings"
    chat_id = Column(String(14), primary_key=True)
    setting = Column(Boolean, default=False, nullable=False)

    def __init__(self, chat_id, disabled):
        self.chat_id = str(chat_id)
        self.setting = disabled

    def __repr__(self):
        return "<NLP setting {} ({})>".format(self.chat_id, self.setting)


NLPSettings.__table__.create(checkfirst=True)

NLP_SETTING_LOCK = threading.RLock()
NLPSTAT_LIST = set()


def enable_nlp(chat_id):
    with NLP_SETTING_LOCK:
        chat = SESSION.query(NLPSettings).get(str(chat_id))
        if not chat:
            chat = NLPSettings(chat_id, True)

        chat.setting = True
        SESSION.add(chat)
        SESSION.commit()
        if str(chat_id) in NLPSTAT_LIST:
            NLPSTAT_LIST.remove(str(chat_id))


def disable_nlp(chat_id):
    with NLP_SETTING_LOCK:
        chat = SESSION.query(NLPSettings).get(str(chat_id))
        if not chat:
            chat = NLPSettings(chat_id, False)

        chat.setting = False
        SESSION.add(chat)
        SESSION.commit()
        NLPSTAT_LIST.add(str(chat_id))


def does_chat_nlp(chat_id):
    return str(chat_id) not in NLPSTAT_LIST



def __load_nlp_stat_list():
    global NLPSTAT_LIST
    try:
        NLPSTAT_LIST = {
            x.chat_id for x in SESSION.query(NLPSettings).all() if not x.setting
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


# Create in memory userid to avoid disk access
__load_nlp_stat_list()
