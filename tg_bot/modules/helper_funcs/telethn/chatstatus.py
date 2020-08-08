from telethon.tl.types import ChannelParticipantsAdmins

from tg_bot.modules.helper_funcs.telethn import IMMUNE_USERS, telethn


async def user_is_ban_protected(user_id: int, message):
    if message.is_private or user_id in (IMMUNE_USERS):
        return True

    return any(
        user_id == user.id
        for user in telethn.iter_participants(
            message.chat_id, filter=ChannelParticipantsAdmins
        )
    )


async def user_is_admin(user_id: int, message):
    if message.is_private:
        return True

    return any(
        user_id == user.id or user_id in IMMUNE_USERS
        for user in telethn.iter_participants(
            message.chat_id, filter=ChannelParticipantsAdmins
        )
    )


async def is_user_admin(user_id: int, chat_id):
    return any(
        user_id == user.id or user_id in IMMUNE_USERS
        for user in telethn.iter_participants(
            chat_id, filter=ChannelParticipantsAdmins
        )
    )


async def haruka_is_admin(chat_id: int):
    haruka = await telethn.get_me()
    return any(
        haruka.id == user.id
        for user in telethn.iter_participants(
            chat_id, filter=ChannelParticipantsAdmins
        )
    )


async def is_user_in_chat(chat_id: int, user_id: int):
    return any(user_id == user.id for user in telethn.iter_participants(chat_id))


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
    status = False
    if message.chat.admin_rights:
        status = message.chat.admin_rights.delete_messages
    return status
