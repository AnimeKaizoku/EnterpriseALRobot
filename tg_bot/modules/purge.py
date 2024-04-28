import contextlib
import logging
from telegram.error import BadRequest
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.ext import CallbackContext, CallbackQueryHandler
from typing import List
from tg_bot.modules.helper_funcs.anonymous import AdminPerms, user_admin
from tg_bot.modules.helper_funcs.chat_status import bot_admin, is_user_admin_callback_query
from tg_bot.modules.helper_funcs.decorators import rate_limit, kigcmd
from tg_bot.modules.log_channel import loggable
from pydantic import BaseModel
from uuid import uuid4
from tg_bot import dispatcher

class DeleteMessageCallback(BaseModel):
    purge_id: str
    chat_id: int
    message_ids: List[int]

DEL_MSG_CB_MAP: List[DeleteMessageCallback] = []

# @kigcallback(pattern=r"purge.*")
@is_user_admin_callback_query
@bot_admin
@rate_limit(40, 60)
@loggable
def purge_confirm(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    message = update.effective_message
    data = query.data
    purge_id = data.split("_")[-1]
    # member = update.effective_chat.get_member(query.from_user.id)
    # if member.status not in ["administrator", "creator"]:
    #     query.answer("You need to be admin to do this.", show_alert=True)
    #     return False
    if data == "purge_cancel":
        message.edit_text("Purge has been cancelled.")
        return f"#PURGE_CANCELLED \n<b>Admin:</b> {query.from_user.first_name}\n<b>Chat:</b> {update.effective_chat.title}\n"

    for entry in DEL_MSG_CB_MAP:
        if entry.purge_id == purge_id:
            try:
                resp = context.bot._request.post(
                f"{context.bot.base_url}/deleteMessages",
                        {
                            "chat_id": entry.chat_id,
                            "message_ids": entry.message_ids
                        },
                )
                logging.debug(resp)
                query.edit_message_text(text="Purge completed.")
                return f"#PURGE_COMPLETED \n<b>Admin:</b> {query.from_user.first_name}\n<b>Chat:</b> {update.effective_chat.title}\n<b>Messages:</b> {len(entry.message_ids)}\n"
            except BadRequest as e:
                if e.message == "Too many message identifiers specified":
                    for msg_id in entry.message_ids:
                        with contextlib.suppress(BadRequest):
                            context.bot.delete_message(chat_id=entry.chat_id, message_id=msg_id)
                    query.edit_message_text(text="Purge completed.")
                    return f"#PURGE_COMPLETED \n<b>Admin:</b> {query.from_user.first_name}\n<b>Chat:</b> {update.effective_chat.title}\n<b>Messages:</b> {len(entry.message_ids)}\n"
                query.edit_message_text(text="Failed to purge")
                return f"#PURGE_FAILED \n<b>Admin:</b> {query.from_user.first_name}\n<b>Chat:</b> {update.effective_chat.title}\n"
    query.edit_message_text(text="Purge failed or purge ID not found.")
    return f"#PURGE_FAILED \n<b>Admin:</b> {query.from_user.first_name}\n<b>Chat:</b> {update.effective_chat.title}\n"


@kigcmd(command='purge')
@bot_admin
@user_admin(AdminPerms.CAN_DELETE_MESSAGES)
@rate_limit(40, 60)
@loggable
def purge_messages_botapi(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    # user_id = update.effective_user.id

    # if not user_is_admin(user_id=user_id, chat_id=chat_id):
    #     update.effective_message.reply_text("You must be an admin to use this command.")
    #     return

    # if not can_delete_messages(chat_id=chat_id):
    #     update.effective_message.reply_text("I don't have permission to delete messages in this chat.")
    #     return

    message_id_from = update.effective_message.reply_to_message.message_id if update.effective_message.reply_to_message else None
    message_id_to = update.effective_message.message_id

    if not message_id_from:
        update.effective_message.reply_text("Reply to the message you want to start purging from.")
        return
    messages_to_delete = []
    try:
        messages_to_delete.extend(iter(range(message_id_from, message_id_to + 1)))
        # resp = context.bot._request.post(
        # f"{context.bot.base_url}/deleteMessages",
        # {
        #     "chat_id": chat_id,
        #     "message_ids": messages_to_delete
        # },
        # )
        # logging.debug(resp)
        entry = DeleteMessageCallback(chat_id=chat_id, message_ids=messages_to_delete, purge_id=str(uuid4()))
        DEL_MSG_CB_MAP.append(entry)
        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Confirm",
                        callback_data=f"purge_confirm_{entry.purge_id}",
                    ),
                    InlineKeyboardButton(
                        text="Cancel", callback_data="purge_cancel"
                    ),
                ]
            ]
        )
        update.effective_message.reply_text(
            f"Purge {len(messages_to_delete)} message(s) from {update.effective_chat.title}? This action cannot be undone.",
            reply_markup=buttons,
            parse_mode=ParseMode.MARKDOWN,
        )
        return f"#PURGE_ATTEMPT \n<b>Admin:</b> {update.effective_user.first_name} \n<b>Messages:</b> {len(messages_to_delete)}\n"
    except Exception as e:
        logging.exception(e)
        update.effective_message.reply_text("An error occurred while purging")

# async def purge_messages(event):
#     start = time.perf_counter()
#     if event.from_id is None:
#         return

#     if not await user_is_admin(
#             user_id=event.sender_id, message=event) and event.from_id not in [
#                 1087968824
#             ]:
#         await event.reply("Only Admins are allowed to use this command")
#         return

#     if not await can_delete_messages(message=event):
#         await event.reply("Can't seem to purge the message")
#         return

#     reply_msg = await event.get_reply_message()
#     if not reply_msg:
#         await event.reply(
#             "Reply to a message to select where to start purging from.")
#         return
#     messages = []
#     message_id = reply_msg.id
#     delete_to = event.message.id

#     messages.append(event.reply_to_msg_id)
#     for msg_id in range(message_id, delete_to + 1):
#         messages.append(msg_id)
#         if len(messages) == 100:
#             await event.client.delete_messages(event.chat_id, messages)
#             messages = []

#     try:
#         await event.client.delete_messages(event.chat_id, messages)
#     except:
#         pass
#     time_ = time.perf_counter() - start
#     text = f"Purged Successfully in {time_:0.2f} Second(s)"
#     await event.respond(text, parse_mode='markdown')


# async def delete_messages(event):
#     if event.from_id is None:
#         return

#     if not await user_is_admin(
#             user_id=event.sender_id, message=event) and event.from_id not in [
#                 1087968824
#             ]:
#         await event.reply("Only Admins are allowed to use this command")
#         return

#     if not await can_delete_messages(message=event):
#         await event.reply("Can't seem to delete this?")
#         return

#     message = await event.get_reply_message()
#     if not message:
#         await event.reply("Whadya want to delete?")
#         return
#     chat = await event.get_input_chat()
#     del_message = [message, event.message]
#     await event.client.delete_messages(chat, del_message)

from tg_bot.modules.language import gs

def get_help(chat):
    return gs(chat, "purge_help")

CALLBACK_QUERY_HANDLER = CallbackQueryHandler(purge_confirm, pattern=r"purge.*")
dispatcher.add_handler(CALLBACK_QUERY_HANDLER)



# PURGE_HANDLER = purge_messages, events.NewMessage(pattern="^[!/]purge$")
# DEL_HANDLER = delete_messages, events.NewMessage(pattern="^[!/]del$")

# telethn.add_event_handler(*PURGE_HANDLER)
# telethn.add_event_handler(*DEL_HANDLER)

__mod_name__ = "Purges"
__command_list__ = ["del", "purge"]
# __handlers__ = [PURGE_HANDLER, DEL_HANDLER]

