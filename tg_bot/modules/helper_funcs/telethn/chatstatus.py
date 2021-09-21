from tg_bot.modules.helper_funcs.telethn import HIGHER_AUTH, telethn
from tg_bot import SUPPORT_USERS, SARDEGNA_USERS, WHITELIST_USERS
from telethon.tl.types import ChannelParticipantsAdmins


async def user_is_ban_protected(user_id: int, message):
    status = False
    if message.is_private or user_id in (HIGHER_AUTH + SUPPORT_USERS + SARDEGNA_USERS + WHITELIST_USERS):
        return True

    async for user in telethn.iter_participants(
            message.chat_id, filter=ChannelParticipantsAdmins):
        if user_id == user.id:
            status = True
            break
    return status


async def user_is_admin(user_id: int, message):
    status = False
    if message.is_private:
        return True

    async for user in telethn.iter_participants(
            message.chat_id, filter=ChannelParticipantsAdmins):
        if user_id == user.id or user_id in HIGHER_AUTH:
            status = True
            break
    return status


async def is_user_admin(user_id: int, chat_id):
    status = False
    async for user in telethn.iter_participants(
            chat_id, filter=ChannelParticipantsAdmins):
        if user_id == user.id or user_id in HIGHER_AUTH:
            status = True
            break
    return status


async def zhongli_is_admin(chat_id: int):
    status = False
    zhongli = await telethn.get_me()
    async for user in telethn.iter_participants(
            chat_id, filter=ChannelParticipantsAdmins):
        if zhongli.id == user.id:
            status = True
            break
    return status


async def is_user_in_chat(chat_id: int, user_id: int):
    status = False
    async for user in telethn.iter_participants(chat_id):
        if user_id == user.id:
            status = True
            break
    return status


async def can_change_info(message):
    status = False
    if message.chat.admin_rights:
        status = message.chat.admin_rights.change_info
    return status


async def can_ban_users(message):
    status = False
    if message.chat.admin_rights:
        status = message.chat.admin_rights.ban_users
    return status


async def can_pin_messages(message):
    status = False
    if message.chat.admin_rights:
        status = message.chat.admin_rights.pin_messages
    return status


async def can_invite_users(message):
    status = False
    if message.chat.admin_rights:
        status = message.chat.admin_rights.invite_users
    return status


async def can_add_admins(message):
    status = False
    if message.chat.admin_rights:
        status = message.chat.admin_rights.add_admins
    return status


async def can_delete_messages(message):

    if message.is_private:
        return True
    elif message.chat.admin_rights:
        status = message.chat.admin_rights.delete_messages
        return status
    else:
        return False
