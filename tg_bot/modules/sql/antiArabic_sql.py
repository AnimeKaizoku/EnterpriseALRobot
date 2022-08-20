import threading
from typing import Union

from sqlalchemy import Column, String, Boolean

from tg_bot.modules.sql import SESSION, BASE


class AntiArabicChatSettings(BASE):
    __tablename__ = "chat_antiarabic_settings"
    chat_id = Column(String(14), primary_key=True)
    antiarabic = Column(Boolean, default=True)

    def __init__(self, chat_id):
        self.chat_id = str(chat_id)

    def __repr__(self):
        return "<Chat AntiArabic settings ({})>".format(self.chat_id)


AntiArabicChatSettings.__table__.create(checkfirst=True)

CHAT_LOCK = threading.RLock()


def chat_antiarabic(chat_id: Union[str, int]) -> bool:
    try:
        chat_setting = SESSION.query(AntiArabicChatSettings).get(str(chat_id))
        if chat_setting:
            return chat_setting.antiarabic
        return False
    finally:
        SESSION.close()


def set_chat_setting(chat_id: Union[int, str], setting: bool):
    with CHAT_LOCK:
        chat_setting = SESSION.query(AntiArabicChatSettings).get(str(chat_id))
        if not chat_setting:
            chat_setting = AntiArabicChatSettings(chat_id)

        chat_setting.antiarabic = setting
        SESSION.add(chat_setting)
        SESSION.commit()


def migrate_chat(old_chat_id, new_chat_id):
    with CHAT_LOCK:
        chat_notes = SESSION.query(AntiArabicChatSettings).filter(
            AntiArabicChatSettings.chat_id == str(old_chat_id)).all()
        for note in chat_notes:
            note.chat_id = str(new_chat_id)
        SESSION.commit()
