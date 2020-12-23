import html
from pyrogram import Client, filters
from pyrogram.errors.exceptions.bad_request_400 import MessageNotModified

from tg_bot import kp, get_entity

ZWS = "\u200B"


def _generate_sexy(entity, ping):
    text = getattr(entity, "title", None)
    if not text:
        text = entity.first_name
        if entity.last_name:
            text += f" {entity.last_name}"
    sexy_text = html.escape(text or "") or "<code>[DELETED]</code>"
    if ping and entity.type in ("private", "bot") and text:
        sexy_text = f'<a href="tg://user?id={entity.id}">{sexy_text}</a>'
    elif entity.username:
        sexy_text = f'<a href="https://t.me/{entity.username}">{sexy_text}</a>'
    elif not ping:
        sexy_text = sexy_text.replace("@", f"@{ZWS}")
    if entity.type == "bot":
        sexy_text += " <code>[BOT]</code>"
    if entity.is_verified:
        sexy_text += " <code>[VERIFIED]</code>"
    if entity.is_support:
        sexy_text += " <code>[SUPPORT]</code>"
    if entity.is_scam:
        sexy_text += " <code>[SCAM]</code>"
    return sexy_text


@kp.on_message(filters.command(["cinfo"], prefixes=["/", "!"]))
async def info(client, message):
    entity = message.chat
    command = message.command
    command.pop(0)
    if command:
        entity = " ".join(command)
    elif not getattr(message.reply_to_message, "empty", True):
        entity = message.reply_to_message.from_user or message.reply_to_message.chat
    try:
        entity, entity_client = await get_entity(client, entity)
    except BaseException as ex:
        await message.reply_text(f"{type(ex).__name__}: {str(ex)}", parse_mode=None)
        return
    text_ping = _generate_sexy(entity, True)
    text_unping = _generate_sexy(entity, False)
    text_ping += f"\n<b>ID:</b> <code>{entity.id}</code>"
    text_unping += f"\n<b>ID:</b> <code>{entity.id}</code>"
    if entity.dc_id:
        text_ping += f"\n<b>DC ID:</b> {entity.dc_id}"
        text_unping += f"\n<b>DC ID:</b> {entity.dc_id}"
    if entity.username:
        text_ping += f"\n<b>Username:</b> @{entity.username}"
        text_unping += f"\n<b>Username:</b> @{ZWS}{entity.username}"
    if entity.members_count:
        text_ping += f"\n<b>Members:</b> {entity.members_count}"
        text_unping += f"\n<b>Members:</b> {entity.members_count}"
    if entity.linked_chat:
        text_ping += f"\n<b>Linked Chat:</b> {_generate_sexy(entity.linked_chat, False)} [<code>{entity.linked_chat.id}</code>]"
        text_unping += f"\n<b>Linked Chat:</b> {_generate_sexy(entity.linked_chat, False)} [<code>{entity.linked_chat.id}</code>]"
    if entity.description:
        text_ping += f"\n<b>Description:</b>\n{html.escape(entity.description)}"
        text_unping += f'\n<b>Description:</b>\n{html.escape(entity.description.replace("@", "@" + ZWS))}'
    reply = await message.reply_text(text_unping, disable_web_page_preview=True)
    if text_ping != text_unping:
        try:
            await reply.edit_text(text_ping, disable_web_page_preview=True)
        except MessageNotModified:
            pass


@kp.on_message(filters.command(["getid"], prefixes=["/", "!"]))
async def id(client, message):
    text_unping = "<b>Chat ID:</b>"
    if message.chat.username:
        text_unping = (
            f'<a href="https://t.me/{message.chat.username}">{text_unping}</a>'
        )
    text_unping += f" <code>{message.chat.id}</code>\n"
    text = "<b>Message ID:</b>"
    if message.link:
        text = f'<a href="{message.link}">{text}</a>'
    text += f" <code>{message.message_id}</code>\n"
    text_unping += text
    if message.from_user:
        text_unping += f'<b><a href="tg://user?id={message.from_user.id}">User ID:</a></b> <code>{message.from_user.id}</code>\n'
    text_ping = text_unping
    reply = message.reply_to_message
    if not getattr(reply, "empty", True):
        text_unping += "\n"
        text = "<b>Replied Message ID:</b>"
        if reply.link:
            text = f'<a href="{reply.link}">{text}</a>'
        text += f" <code>{reply.message_id}</code>\n"
        text_unping += text
        text_ping = text_unping
        if reply.from_user:
            text = "<b>Replied User ID:</b>"
            if reply.from_user.username:
                text = f'<a href="https://t.me/{reply.from_user.username}">{text}</a>'
            text += f" <code>{reply.from_user.id}</code>\n"
            text_unping += text
            text_ping += f'<b><a href="tg://user?id={reply.from_user.id}">Replied User ID:</a></b> <code>{reply.from_user.id}</code>\n'
        if reply.forward_from:
            text_unping += "\n"
            text = "<b>Forwarded User ID:</b>"
            if reply.forward_from.username:
                text = (
                    f'<a href="https://t.me/{reply.forward_from.username}">{text}</a>'
                )
            text += f" <code>{reply.forward_from.id}</code>\n"
            text_unping += text
            text_ping += f'\n<b><a href="tg://user?id={reply.forward_from.id}">Forwarded User ID:</a></b> <code>{reply.forward_from.id}</code>\n'
    reply = await message.reply_text(text_unping, disable_web_page_preview=True)
    if text_unping != text_ping:
        await reply.edit_text(text_ping, disable_web_page_preview=True)
