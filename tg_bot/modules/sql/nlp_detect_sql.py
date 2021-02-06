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

class NLPAction(BASE):
    __tablename__ = "nlp_action"
    chat_id = Column(String(14), primary_key=True)
    action_type = Column(Integer, default=1)
    value = Column(UnicodeText, default="0")

    def __init__(self, chat_id, action_type=1, value="0"):
        self.chat_id = str(chat_id)
        self.action_type = action_type
        self.value = value

    def __repr__(self):
        return "<{} will executing {} for NLP.>".format(self.chat_id, self.action_type)



NLPAction.__table__.create(checkfirst=True)
NLPSettings.__table__.create(checkfirst=True)

NLP_SETTING_LOCK = threading.RLock()
NLP_MODE_LOCK = threading.RLock()
NLPSETTING_LIST = set()

def enable_nlp_bans(chat_id):
    with NLP_SETTING_LOCK:
        chat = SESSION.query(NLPSettings).get(str(chat_id))
        if not chat:
            chat = NLPSettings(chat_id, True)

        chat.setting = True
        SESSION.add(chat)
        SESSION.commit()
        if str(chat_id) in NLPSETTING_LIST:
            NLPSETTING_LIST.remove(str(chat_id))


def disable_nlp_bans(chat_id):
    with NLP_SETTING_LOCK:
        chat = SESSION.query(NLPSettings).get(str(chat_id))
        if not chat:
            chat = NLPSettings(chat_id, False)

        chat.setting = False
        SESSION.add(chat)
        SESSION.commit()
        NLPSETTING_LIST.add(str(chat_id))

def set_action(chat_id, action_type, value):
    # for action_type
    # 1 = ban
    # 2 = notify
    with NLP_MODE_LOCK:
        curr_setting = SESSION.query(NLPAction).get(str(chat_id))
        if not curr_setting:
            curr_setting = NLPAction(
                chat_id, action_type=int(action_type), value=value
            )

        curr_setting.action_type = int(action_type)
        curr_setting.value = str(value)

        SESSION.add(curr_setting)
        SESSION.commit()

def get_nlp_mode(chat_id):
    try:
        setting = SESSION.query(NLPAction).get(str(chat_id))
        if setting:
            return setting.action_type, setting.value
        else:
            return 1, "0"

    finally:
        SESSION.close()

def does_chat_nlp_ban(chat_id):
    return str(chat_id) not in NLPSETTING_LIST

def __load_nlp_stat_list():
    global NLPSETTING_LIST
    try:
        NLPSETTING_LIST = {
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
