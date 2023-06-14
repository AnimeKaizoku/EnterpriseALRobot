import csv
import json
import os
import re
import time
import uuid
from io import BytesIO

import FallenRobot.modules.sql.feds_sql as sql
from FallenRobot import (EVENT_LOGS, LOGGER, OWNER_ID, DRAGONS, DEV_USERS,
                          DEMONS, TIGERS, WOLVES, dispatcher)
from FallenRobot.modules.disable import DisableAbleCommandHandler
from FallenRobot.modules.helper_funcs.alternate import send_message
from FallenRobot.modules.helper_funcs.chat_status import is_user_admin
from FallenRobot.modules.helper_funcs.extraction import (extract_unt_fedban,
                                                          extract_user,
                                                          extract_user_fban)
from FallenRobot.modules.helper_funcs.string_handling import markdown_parser
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, MessageEntity,
                      ParseMode, Update)
from telegram.error import BadRequest, TelegramError, Unauthorized
from telegram.ext import (CallbackContext, CallbackQueryHandler, CommandHandler,
                          run_async)
from telegram.utils.helpers import (mention_html, mention_markdown)

# Hello bot owner, I spended for feds many hours of my life, Please don't remove this if you still respect MrYacha and peaktogoo and AyraHikari too
# Federation by MrYacha 2018-2019
# Federation rework by Mizukito Akito 2019
# Federation update v2 by Ayra Hikari 2019
# Time spended on feds = 10h by #MrYacha
# Time spended on reworking on the whole feds = 22+ hours by @peaktogoo
# Time spended on updating version to v2 = 26+ hours by @AyraHikari
# Total spended for making this features is 68+ hours
# LOGGER.info("Original federation module by MrYacha, reworked by Mizukito Akito (@peaktogoo) on Telegram.")

FBAN_ERRORS = {
    "El usuario es administrador del grupo", "Chat not found",
    "No hay suficientes derechos para restringir/no restringir al miembro del chat",
    "User_not_participant", "Peer_id_invalid", "Se desactivó el chat grupal",
    "Necesita invitar a un usuario para sacarlo de un grupo básico",
    "Chat_admin_required",
    "Solo el creador de un grupo básico puede expulsar a los administradores del grupo",
    "Channel_private", "Not in the chat", "No tiene derecho a enviar un mensaje"
}

UNFBAN_ERRORS = {
    "El usuario es administrador del grupo", "Chat not found",
    "No hay suficientes derechos para restringir/no restringir al miembro del chat",
    "User_not_participant",
    "El método está disponible solo para supergrupos y chats de canal",
    "Not in the chat", "Channel_private", "Chat_admin_required",
    "No tiene derecho a enviar un mensaje"
}


@run_async
def new_fed(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    if chat.type != "private":
        update.effective_message.reply_text(
            "Federations can only be created by privately messaging me.")
        return
    if len(message.text) == 1:
        send_message(update.effective_message,
                     "Please write the name of the federation!")
        return
    fednam = message.text.split(None, 1)[1]
    if not fednam == '':
        fed_id = str(uuid.uuid4())
        fed_name = fednam
        LOGGER.info(fed_id)

        # Currently only for creator
        #if fednam == 'Team Nusantara Disciplinary Circle':
        #fed_id = "TeamNusantaraDevs"

        x = sql.new_fed(user.id, fed_name, fed_id)
        if not x:
            update.effective_message.reply_text(
                "¡No se puede federar! Comuníquese con @{SUPPORT_CHAT} si el problema persiste."
            )
            return

        update.effective_message.reply_text("*Ha logrado crear una nueva federación!*"\
                 "\nNombre: `{}`"\
                 "\nID: `{}`"
                 "\n\nUtilice el siguiente comando para unirse a la federación:"
                 "\n`/joinfed {}`".format(fed_name, fed_id, fed_id), parse_mode=ParseMode.MARKDOWN)
        try:
            bot.send_message(
                EVENT_LOGS,
                "Nueva federación: <b>{}</b>\nID: <pre>{}</pre>".format(
                    fed_name, fed_id),
                parse_mode=ParseMode.HTML)
        except:
            LOGGER.warning("Cannot send a message to EVENT_LOGS")
    else:
        update.effective_message.reply_text(
            "Escriba el nombre de la federación")


@run_async
def del_fed(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    if chat.type != "private":
        update.effective_message.reply_text(
            "Las federaciones solo se pueden eliminar enviándome un mensaje en privado.")
        return
    if args:
        is_fed_id = args[0]
        getinfo = sql.get_fed_info(is_fed_id)
        if getinfo is False:
            update.effective_message.reply_text(
                "Esta federación no existe.")
            return
        if int(getinfo['owner']) == int(user.id) or int(user.id) == OWNER_ID:
            fed_id = is_fed_id
        else:
            update.effective_message.reply_text(
                "Solo los propietarios de federaciones pueden hacer esto!")
            return
    else:
        update.effective_message.reply_text("Que debo borrar?")
        return

    if is_user_fed_owner(fed_id, user.id) is False:
        update.effective_message.reply_text(
            "Solo los propietarios de federaciones pueden hacer esto!")
        return

    update.effective_message.reply_text(
        "Seguro que quiere eliminar su federación? Esto no se puede revertir, perderá toda su lista de prohibiciones y '{}' se perderá permanentemente."
        .format(getinfo['fname']),
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(
                text="⚠️ Eliminar Federación ⚠️",
                callback_data="rmfed_{}".format(fed_id))
        ], [InlineKeyboardButton(text="❌ Cancelar ❌",
                                 callback_data="rmfed_cancel")]]))


@run_async
def fed_chat(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    fed_id = sql.get_fed_id(chat.id)

    user_id = update.effective_message.from_user.id
    if not is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text(
            "Debes ser un administrador para ejecutar este comando")
        return

    if not fed_id:
        update.effective_message.reply_text(
            "Este grupo no está en ninguna federación!")
        return

    user = update.effective_user
    chat = update.effective_chat
    info = sql.get_fed_info(fed_id)

    text = "Este grupo es parte de la siguiente federación:"
    text += "\n{} (ID: <code>{}</code>)".format(info['fname'], fed_id)

    update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


@run_async
def join_fed(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == 'private':
        send_message(update.effective_message,
                     "Este comando es específico del grupo, no de nuestro grupo privado!")
        return

    message = update.effective_message
    administrators = chat.get_administrators()
    fed_id = sql.get_fed_id(chat.id)

    if user.id in DRAGONS:
        pass
    else:
        for admin in administrators:
            status = admin.status
            if status == "creator":
                if str(admin.user.id) == str(user.id):
                    pass
                else:
                    update.effective_message.reply_text(
                        "Solo los creadores de los grupos pueden usar este comando!")
                    return
    if fed_id:
        message.reply_text("No puedes unirte a dos federaciones desde un grupo")
        return

    if len(args) >= 1:
        getfed = sql.search_fed_by_id(args[0])
        if getfed is False:
            message.reply_text("Por favor ingresa un ID de federación válido")
            return

        x = sql.chat_join_fed(args[0], chat.title, chat.id)
        if not x:
            message.reply_text(
                "No se pudo unir a la federación! Comuníquese con @{SUPPORT_CHAT} si el problema persiste!"
            )
            return

        get_fedlog = sql.get_fed_log(args[0])
        if get_fedlog:
            if eval(get_fedlog):
                bot.send_message(
                    get_fedlog,
                    "Chat *{}* has joined the federation *{}*".format(
                        chat.title, getfed['fname']),
                    parse_mode="markdown")

        message.reply_text("Este grupo se ha unido a la federación: {}!".format(
            getfed['fname']))


@run_async
def leave_fed(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == 'private':
        send_message(update.effective_message,
                     "Este comando es específico del grupo, no de nuestro chat privado!")
        return

    fed_id = sql.get_fed_id(chat.id)
    fed_info = sql.get_fed_info(fed_id)

    # administrators = chat.get_administrators().status
    getuser = bot.get_chat_member(chat.id, user.id).status
    if getuser in 'creator' or user.id in DRAGONS:
        if sql.chat_leave_fed(chat.id) is True:
            get_fedlog = sql.get_fed_log(fed_id)
            if get_fedlog:
                if eval(get_fedlog):
                    bot.send_message(
                        get_fedlog,
                        "Chat *{}* has left the federation *{}*".format(
                            chat.title, fed_info['fname']),
                        parse_mode="markdown")
            send_message(
                update.effective_message,
                "Este grupo ha dejado la federación {}!".format(
                    fed_info['fname']))
        else:
            update.effective_message.reply_text(
                "Cómo puedes dejar una federación a la que nunca te uniste?!")
    else:
        update.effective_message.reply_text(
            "Solo los creadores de grupo pueden usar este comando!")


@run_async
def user_join_fed(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    if chat.type == 'private':
        send_message(update.effective_message,
                     "Este comando es específico del grupo, no de nuestro chat privado!")
        return

    fed_id = sql.get_fed_id(chat.id)

    if is_user_fed_owner(fed_id, user.id) or user.id in DRAGONS:
        user_id = extract_user(msg, args)
        if user_id:
            user = bot.get_chat(user_id)
        elif not msg.reply_to_message and not args:
            user = msg.from_user
        elif not msg.reply_to_message and (
                not args or
            (len(args) >= 1 and not args[0].startswith("@") and
             not args[0].isdigit() and
             not msg.parse_entities([MessageEntity.TEXT_MENTION]))):
            msg.reply_text("No puedo extraer al usuario de este mensaje")
            return
        else:
            LOGGER.warning('error')
        getuser = sql.search_user_in_fed(fed_id, user_id)
        fed_id = sql.get_fed_id(chat.id)
        info = sql.get_fed_info(fed_id)
        get_owner = eval(info['fusers'])['owner']
        get_owner = bot.get_chat(get_owner).id
        if user_id == get_owner:
            update.effective_message.reply_text(
                "Sabes que el usuario es el propietario de la federación, verdad? VERDAD?"
            )
            return
        if getuser:
            update.effective_message.reply_text(
                "No puedo promover usuarios que ya son administradores de la federación! Puedes eliminarlos si quieres!"
            )
            return
        if user_id == bot.id:
            update.effective_message.reply_text(
                "Ya soy administradora de federaciones en todas las federaciones.!")
            return
        res = sql.user_join_fed(fed_id, user_id)
        if res:
            update.effective_message.reply_text("Promovido exitosamente!")
        else:
            update.effective_message.reply_text("No se pudo promover!")
    else:
        update.effective_message.reply_text(
            "Solo los propietarios de federaciones pueden hacer eso!")


@run_async
def user_demote_fed(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == 'private':
        send_message(update.effective_message,
                     "Este comando es específico del grupo, no de nuestro chat privado!")
        return

    fed_id = sql.get_fed_id(chat.id)

    if is_user_fed_owner(fed_id, user.id):
        msg = update.effective_message
        user_id = extract_user(msg, args)
        if user_id:
            user = bot.get_chat(user_id)

        elif not msg.reply_to_message and not args:
            user = msg.from_user

        elif not msg.reply_to_message and (
                not args or
            (len(args) >= 1 and not args[0].startswith("@") and
             not args[0].isdigit() and
             not msg.parse_entities([MessageEntity.TEXT_MENTION]))):
            msg.reply_text("No puedo extraer al usuario de este mensaje")
            return
        else:
            LOGGER.warning('error')

        if user_id == bot.id:
            update.effective_message.reply_text(
                "La cosa de la que estás tratando de degradarme no funcionará sin mí! Solo digo."
            )
            return

        if sql.search_user_in_fed(fed_id, user_id) is False:
            update.effective_message.reply_text(
                "No puedo degradar a las personas que no son administradores de la federación!")
            return

        res = sql.user_demote_fed(fed_id, user_id)
        if res is True:
            update.effective_message.reply_text("Degradado de administrador de la federación!")
        else:
            update.effective_message.reply_text("No se pudo degradar!")
    else:
        update.effective_message.reply_text(
            "Solo los propietarios de federaciones pueden hacer eso!")
        return


@run_async
def fed_info(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    if args:
        fed_id = args[0]
        info = sql.get_fed_info(fed_id)
    else:
        fed_id = sql.get_fed_id(chat.id)
        if not fed_id:
            send_message(update.effective_message,
                         "Este grupo no está en ninguna federación!")
            return
        info = sql.get_fed_info(fed_id)

    if is_user_fed_admin(fed_id, user.id) is False:
        update.effective_message.reply_text(
            "Solo un administrador de la federación puede hacer esto!")
        return

    owner = bot.get_chat(info['owner'])
    try:
        owner_name = owner.first_name + " " + owner.last_name
    except:
        owner_name = owner.first_name
    FEDADMIN = sql.all_fed_users(fed_id)
    FEDADMIN.append(int(owner.id))
    TotalAdminFed = len(FEDADMIN)

    user = update.effective_user
    chat = update.effective_chat
    info = sql.get_fed_info(fed_id)

    text = "<b>ℹ️ Información de la Federación:</b>"
    text += "\nID de la Federación: <code>{}</code>".format(fed_id)
    text += "\nNombre: {}".format(info['fname'])
    text += "\nCreador: {}".format(mention_html(owner.id, owner_name))
    text += "\nAdministradores: <code>{}</code>".format(TotalAdminFed)
    getfban = sql.get_all_fban_users(fed_id)
    text += "\nTotal de usuarios baneados: <code>{}</code>".format(len(getfban))
    getfchat = sql.all_fed_chats(fed_id)
    text += "\nN° de grupos en esta federación: <code>{}</code>".format(
        len(getfchat))

    update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


@run_async
def fed_admin(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == 'private':
        send_message(update.effective_message,
                     "Este comando es específico del grupo, no de nuestro chat privado!")
        return

    fed_id = sql.get_fed_id(chat.id)

    if not fed_id:
        update.effective_message.reply_text(
            "Este grupo no está en ninguna federación!")
        return

    if is_user_fed_admin(fed_id, user.id) is False:
        update.effective_message.reply_text(
            "Solo los administradores de la federación pueden hacer esto!")
        return

    user = update.effective_user
    chat = update.effective_chat
    info = sql.get_fed_info(fed_id)

    text = "<b>Administrador de la federación {}:</b>\n\n".format(info['fname'])
    text += "👑 Propietario:\n"
    owner = bot.get_chat(info['owner'])
    try:
        owner_name = owner.first_name + " " + owner.last_name
    except:
        owner_name = owner.first_name
    text += " • {}\n".format(mention_html(owner.id, owner_name))

    members = sql.all_fed_members(fed_id)
    if len(members) == 0:
        text += "\n🔱 No hay administradores en esta federación"
    else:
        text += "\n🔱 Administradores:\n"
        for x in members:
            user = bot.get_chat(x)
            text += " • {}\n".format(mention_html(user.id, user.first_name))

    update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


@run_async
def fed_ban(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == 'private':
        send_message(update.effective_message,
                     "Este comando es específico del grupo, no de nuestro chat privado!")
        return

    fed_id = sql.get_fed_id(chat.id)

    if not fed_id:
        update.effective_message.reply_text(
            "Este grupo no es parte de ninguna federación!")
        return

    info = sql.get_fed_info(fed_id)
    getfednotif = sql.user_feds_report(info['owner'])

    if is_user_fed_admin(fed_id, user.id) is False:
        update.effective_message.reply_text(
            "Solo los administradores de la federación pueden hacer esto!")
        return

    message = update.effective_message

    user_id, reason = extract_unt_fedban(message, args)

    fban, fbanreason, fbantime = sql.get_fban_user(fed_id, user_id)

    if not user_id:
        message.reply_text("No pareces referirte a un usuario")
        return

    if user_id == bot.id:
        message.reply_text(
            "Qué es más divertido que patear al creador del grupo? Autosacrificio.")
        return

    if is_user_fed_owner(fed_id, user_id) is True:
        message.reply_text("Por qué probaste la federación fban?")
        return

    if is_user_fed_admin(fed_id, user_id) is True:
        message.reply_text("Él es un administrador de la federación, no puedo banearlo de la federación.")
        return

    if user_id == OWNER_ID:
        message.reply_text("Mi dueño no puede ser baneado de una federación!")
        return

    if int(user_id) in DRAGONS:
        message.reply_text("Los hylians no pueden ser baneados de la federación!")
        return

    if int(user_id) in DEMONS:
        message.reply_text("Los sheikas no pueden ser baneados de la federación!")
        return

    if int(user_id) in TIGERS:
        message.reply_text("Los zoras no pueden ser baneados de la federación!")
        return

    if int(user_id) in WOLVES:
        message.reply_text("Los gorons no pueden ser baneados de la federación!")
        return

    try:
        user_chat = bot.get_chat(user_id)
        isvalid = True
        fban_user_id = user_chat.id
        fban_user_name = user_chat.first_name
        fban_user_lname = user_chat.last_name
        fban_user_uname = user_chat.username
    except BadRequest as excp:
        if not str(user_id).isdigit():
            send_message(update.effective_message, excp.message)
            return
        elif len(str(user_id)) != 9:
            send_message(update.effective_message, "Eso no es un usuario!")
            return
        isvalid = False
        fban_user_id = int(user_id)
        fban_user_name = "user({})".format(user_id)
        fban_user_lname = None
        fban_user_uname = None

    if isvalid and user_chat.type != 'private':
        send_message(update.effective_message, "Eso no es un usuario!")
        return

    if isvalid:
        user_target = mention_html(fban_user_id, fban_user_name)
    else:
        user_target = fban_user_name

    if fban:
        fed_name = info['fname']
        #https://t.me/OnePunchSupport/41606 // https://t.me/OnePunchSupport/41619
        #starting = "The reason fban is replaced for {} in the Federation <b>{}</b>.".format(user_target, fed_name)
        #send_message(update.effective_message, starting, parse_mode=ParseMode.HTML)

        #if reason == "":
        #    reason = "No reason given."

        temp = sql.un_fban_user(fed_id, fban_user_id)
        if not temp:
            message.reply_text("No se pudo actualizar el motivo de ban de la federación!")
            return
        x = sql.fban_user(fed_id, fban_user_id, fban_user_name, fban_user_lname,
                          fban_user_uname, reason, int(time.time()))
        if not x:
            message.reply_text(
                "No se pudo expulsar de la federación! Si este problema continúa, comuníquese con @{SUPPORT_CHAT}."
            )
            return

        fed_chats = sql.all_fed_chats(fed_id)
        # Will send to current chat
        bot.send_message(chat.id, "<b>Razón de baneo de la federación actualizada</b>" \
              "\n<b>Federación:</b> {}" \
              "\n<b>Administrador de la federación:</b> {}" \
              "\n<b>Usuario:</b> {}" \
              "\n<b>ID de Usuario:</b> <code>{}</code>" \
              "\n<b>Razón:</b> {}".format(fed_name, mention_html(user.id, user.first_name), user_target, fban_user_id, reason), parse_mode="HTML")
        # Send message to owner if fednotif is enabled
        if getfednotif:
            bot.send_message(info['owner'], "<b>Razón de baneo de la federación actualizada</b>" \
                 "\n<b>Federación:</b> {}" \
                 "\n<b>Administrador de la federación:</b> {}" \
                 "\n<b>Usuario:</b> {}" \
                 "\n<b>ID de Usuario:</b> <code>{}</code>" \
                 "\n<b>Razón:</b> {}".format(fed_name, mention_html(user.id, user.first_name), user_target, fban_user_id, reason), parse_mode="HTML")
        # If fedlog is set, then send message, except fedlog is current chat
        get_fedlog = sql.get_fed_log(fed_id)
        if get_fedlog:
            if int(get_fedlog) != int(chat.id):
                bot.send_message(get_fedlog, "<b>Razón de baneo de la federación actualizada</b>" \
                    "\n<b>Federación:</b> {}" \
                    "\n<b>Administrador de la federación:</b> {}" \
                    "\n<b>Usuario:</b> {}" \
                    "\n<b>ID de Usuario:</b> <code>{}</code>" \
                    "\n<b>Razón:</b> {}".format(fed_name, mention_html(user.id, user.first_name), user_target, fban_user_id, reason), parse_mode="HTML")
        for fedschat in fed_chats:
            try:
                # Do not spam all fed chats
                """
				bot.send_message(chat, "<b>Razón de baneo de la federación actualizada</b>" \
							 "\n<b>Federación:</b> {}" \
							 "\n<b>Administrador de la federación:</b> {}" \
							 "\n<b>Usuario:</b> {}" \
							 "\n<b>ID de Usuario:</b> <code>{}</code>" \
							 "\n<b>Razón:</b> {}".format(fed_name, mention_html(user.id, user.first_name), user_target, fban_user_id, reason), parse_mode="HTML")
				"""
                bot.kick_chat_member(fedschat, fban_user_id)
            except BadRequest as excp:
                if excp.message in FBAN_ERRORS:
                    try:
                        dispatcher.bot.getChat(fedschat)
                    except Unauthorized:
                        sql.chat_leave_fed(fedschat)
                        LOGGER.info(
                            "El chat {} ha abandonado la federación {} porque me echaron"
                            .format(fedschat, info['fname']))
                        continue
                elif excp.message == "User_id_invalid":
                    break
                else:
                    LOGGER.warning("No se puedo banear de la federación en {} porque: {}".format(
                        chat, excp.message))
            except TelegramError:
                pass
        # Also do not spam all fed admins
        """
		send_to_list(bot, FEDADMIN,
				 "<b>Razón de baneo de la federación actualizada</b>" \
							 "\n<b>Federación:</b> {}" \
							 "\n<b>Administrador de la federación:</b> {}" \
							 "\n<b>Usuario:</b> {}" \
							 "\n<b>ID de Usuario:</b> <code>{}</code>" \
							 "\n<b>Razón:</b> {}".format(fed_name, mention_html(user.id, user.first_name), user_target, fban_user_id, reason), 
							html=True)
		"""

        # Fban for fed subscriber
        subscriber = list(sql.get_subscriber(fed_id))
        if len(subscriber) != 0:
            for fedsid in subscriber:
                all_fedschat = sql.all_fed_chats(fedsid)
                for fedschat in all_fedschat:
                    try:
                        bot.kick_chat_member(fedschat, fban_user_id)
                    except BadRequest as excp:
                        if excp.message in FBAN_ERRORS:
                            try:
                                dispatcher.bot.getChat(fedschat)
                            except Unauthorized:
                                targetfed_id = sql.get_fed_id(fedschat)
                                sql.unsubs_fed(fed_id, targetfed_id)
                                LOGGER.info(
                                    "El chat {} anuló la federación {} porque me echaron"
                                    .format(fedschat, info['fname']))
                                continue
                        elif excp.message == "User_id_invalid":
                            break
                        else:
                            LOGGER.warning(
                                "No se puede banear de la federación en {} porque: {}".format(
                                    fedschat, excp.message))
                    except TelegramError:
                        pass
        #send_message(update.effective_message, "Fedban Reason has been updated.")
        return

    fed_name = info['fname']

    #starting = "Starting a federation ban for {} in the Federation <b>{}</b>.".format(
    #    user_target, fed_name)
    #update.effective_message.reply_text(starting, parse_mode=ParseMode.HTML)

    #if reason == "":
    #    reason = "No reason given."

    x = sql.fban_user(fed_id, fban_user_id, fban_user_name, fban_user_lname,
                      fban_user_uname, reason, int(time.time()))
    if not x:
        message.reply_text(
            "No se pudo expulsar de la federación! Si este problema continúa, comuníquese con @{SUPPORT_CHAT}."
        )
        return

    fed_chats = sql.all_fed_chats(fed_id)
    # Will send to current chat
    bot.send_message(chat.id, "<b>Razón de baneo de la federación actualizada</b>" \
          "\n<b>Federación:</b> {}" \
          "\n<b>Administrador de la federación:</b> {}" \
          "\n<b>Usuario:</b> {}" \
          "\n<b>ID de Usuario:</b> <code>{}</code>" \
          "\n<b>Razón:</b> {}".format(fed_name, mention_html(user.id, user.first_name), user_target, fban_user_id, reason), parse_mode="HTML")
    # Send message to owner if fednotif is enabled
    if getfednotif:
        bot.send_message(info['owner'], "<b>Razón de baneo de la federación actualizada</b>" \
             "\n<b>Federación:</b> {}" \
             "\n<b>Administrador de la federación:</b> {}" \
             "\n<b>Usuario:</b> {}" \
             "\n<b>ID de Usuario:</b> <code>{}</code>" \
             "\n<b>Razón:</b> {}".format(fed_name, mention_html(user.id, user.first_name), user_target, fban_user_id, reason), parse_mode="HTML")
    # If fedlog is set, then send message, except fedlog is current chat
    get_fedlog = sql.get_fed_log(fed_id)
    if get_fedlog:
        if int(get_fedlog) != int(chat.id):
            bot.send_message(get_fedlog, "<b>Razón de baneo de la federación actualizada</b>" \
                "\n<b>Federación:</b> {}" \
                "\n<b>Administrador de la federación:</b> {}" \
                "\n<b>Usuario:</b> {}" \
                "\n<b>ID de Usuario:</b> <code>{}</code>" \
                "\n<b>Razón:</b> {}".format(fed_name, mention_html(user.id, user.first_name), user_target, fban_user_id, reason), parse_mode="HTML")
    chats_in_fed = 0
    for fedschat in fed_chats:
        chats_in_fed += 1
        try:
            # Do not spamming all fed chats
            """
			bot.send_message(chat, "<b>Razón de baneo de la federación actualizada</b>" \
							"\n<b>Federación:</b> {}" \
							"\n<b>Administrador de la federación:</b> {}" \
							"\n<b>Usuario:</b> {}" \
							"\n<b>ID de Usuario:</b> <code>{}</code>" \
							"\n<b>Razón:</b> {}".format(fed_name, mention_html(user.id, user.first_name), user_target, fban_user_id, reason), parse_mode="HTML")
			"""
            bot.kick_chat_member(fedschat, fban_user_id)
        except BadRequest as excp:
            if excp.message in FBAN_ERRORS:
                pass
            elif excp.message == "User_id_invalid":
                break
            else:
                LOGGER.warning("Could not fban on {} because: {}".format(
                    chat, excp.message))
        except TelegramError:
            pass

    # Also do not spamming all fed admins
        """
		send_to_list(bot, FEDADMIN,
				 "<b>Razón de baneo de la federación actualizada</b>" \
							 "\n<b>Federación:</b> {}" \
							 "\n<b>Administrador de la federación:</b> {}" \
							 "\n<b>Usuario:</b> {}" \
							 "\n<b>ID de Usuario:</b> <code>{}</code>" \
							 "\n<b>Razón:</b> {}".format(fed_name, mention_html(user.id, user.first_name), user_target, fban_user_id, reason), 
							html=True)
		"""

        # Fban for fed subscriber
        subscriber = list(sql.get_subscriber(fed_id))
        if len(subscriber) != 0:
            for fedsid in subscriber:
                all_fedschat = sql.all_fed_chats(fedsid)
                for fedschat in all_fedschat:
                    try:
                        bot.kick_chat_member(fedschat, fban_user_id)
                    except BadRequest as excp:
                        if excp.message in FBAN_ERRORS:
                            try:
                                dispatcher.bot.getChat(fedschat)
                            except Unauthorized:
                                targetfed_id = sql.get_fed_id(fedschat)
                                sql.unsubs_fed(fed_id, targetfed_id)
                                LOGGER.info(
                                    "El chat {} anuló la federación {} porque me echaron"
                                    .format(fedschat, info['fname']))
                                continue
                        elif excp.message == "User_id_invalid":
                            break
                        else:
                            LOGGER.warning(
                                "No se pudo banear de la federación en {} porque: {}".format(
                                    fedschat, excp.message))
                    except TelegramError:
                        pass
    #if chats_in_fed == 0:
    #    send_message(update.effective_message, "Fedban affected 0 chats. ")
    #elif chats_in_fed > 0:
    #    send_message(update.effective_message,
    #                 "Fedban affected {} chats. ".format(chats_in_fed))


@run_async
def unfban(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    if chat.type == 'private':
        send_message(update.effective_message,
                     "Este comando es específico del grupo, no de nuestro chat privado!")
        return

    fed_id = sql.get_fed_id(chat.id)

    if not fed_id:
        update.effective_message.reply_text(
            "Este grupo no es parte de ninguna federación!")
        return

    info = sql.get_fed_info(fed_id)
    getfednotif = sql.user_feds_report(info['owner'])

    if is_user_fed_admin(fed_id, user.id) is False:
        update.effective_message.reply_text(
            "Solo los administradores de la federación pueden hacer esto!")
        return

    user_id = extract_user_fban(message, args)
    if not user_id:
        message.reply_text("No pareces referirte a un usuario.")
        return

    try:
        user_chat = bot.get_chat(user_id)
        isvalid = True
        fban_user_id = user_chat.id
        fban_user_name = user_chat.first_name
        fban_user_lname = user_chat.last_name
        fban_user_uname = user_chat.username
    except BadRequest as excp:
        if not str(user_id).isdigit():
            send_message(update.effective_message, excp.message)
            return
        elif len(str(user_id)) != 9:
            send_message(update.effective_message, "Eso no es un usuario!")
            return
        isvalid = False
        fban_user_id = int(user_id)
        fban_user_name = "user({})".format(user_id)
        fban_user_lname = None
        fban_user_uname = None

    if isvalid and user_chat.type != 'private':
        message.reply_text("Eso no es un usuario!")
        return

    if isvalid:
        user_target = mention_html(fban_user_id, fban_user_name)
    else:
        user_target = fban_user_name

    fban, fbanreason, fbantime = sql.get_fban_user(fed_id, fban_user_id)
    if fban is False:
        message.reply_text("Este usuario no está baneado de la federación!")
        return

    banner = update.effective_user

    message.reply_text("Daré otra oportunidad a {} en esta federación".format(
        user_chat.first_name))

    chat_list = sql.all_fed_chats(fed_id)
    # Will send to current chat
    bot.send_message(chat.id, "<b>Desbaneo de la Federación</b>" \
          "\n<b>Federación:</b> {}" \
          "\n<b>Administrador de la federación:</b> {}" \
          "\n<b>Usuario:</b> {}" \
          "\n<b>ID de Usuario:</b> <code>{}</code>".format(info['fname'], mention_html(user.id, user.first_name), user_target, fban_user_id), parse_mode="HTML")
    # Send message to owner if fednotif is enabled
    if getfednotif:
        bot.send_message(info['owner'], "<b>Desbaneo de la Federación</b>" \
             "\n<b>Federación:</b> {}" \
             "\n<b>Administrador de la federación:</b> {}" \
             "\n<b>Usuario:</b> {}" \
             "\n<b>ID de Usuario:</b> <code>{}</code>".format(info['fname'], mention_html(user.id, user.first_name), user_target, fban_user_id), parse_mode="HTML")
    # If fedlog is set, then send message, except fedlog is current chat
    get_fedlog = sql.get_fed_log(fed_id)
    if get_fedlog:
        if int(get_fedlog) != int(chat.id):
            bot.send_message(get_fedlog, "<b>Desbaneo de la Federación</b>" \
                "\n<b>Federación:</b> {}" \
                "\n<b>Administrador de la federación:</b> {}" \
                "\n<b>Usuario:</b> {}" \
                "\n<b>ID de Usuario:</b> <code>{}</code>".format(info['fname'], mention_html(user.id, user.first_name), user_target, fban_user_id), parse_mode="HTML")
    unfbanned_in_chats = 0
    for fedchats in chat_list:
        unfbanned_in_chats += 1
        try:
            member = bot.get_chat_member(fedchats, user_id)
            if member.status == 'kicked':
                bot.unban_chat_member(fedchats, user_id)
            # Do not spamming all fed chats
            """
			bot.send_message(chat, "<b>Desbaneo de la Federación</b>" \
						 "\n<b>Federación:</b> {}" \
						 "\n<b>Administrador de la federación:</b> {}" \
						 "\n<b>Usuario:</b> {}" \
						 "\n<b>ID de Usuario:</b> <code>{}</code>".format(info['fname'], mention_html(user.id, user.first_name), user_target, fban_user_id), parse_mode="HTML")
			"""
        except BadRequest as excp:
            if excp.message in UNFBAN_ERRORS:
                pass
            elif excp.message == "User_id_invalid":
                break
            else:
                LOGGER.warning("No se pudo banear de la federación en {} porque: {}".format(
                    chat, excp.message))
        except TelegramError:
            pass

    try:
        x = sql.un_fban_user(fed_id, user_id)
        if not x:
            send_message(
                update.effective_message,
                "Falló el desbaneo, es posible que este usuario ya esté desbaneado por la federación!")
            return
    except:
        pass

    # UnFban for fed subscriber
    subscriber = list(sql.get_subscriber(fed_id))
    if len(subscriber) != 0:
        for fedsid in subscriber:
            all_fedschat = sql.all_fed_chats(fedsid)
            for fedschat in all_fedschat:
                try:
                    bot.unban_chat_member(fedchats, user_id)
                except BadRequest as excp:
                    if excp.message in FBAN_ERRORS:
                        try:
                            dispatcher.bot.getChat(fedschat)
                        except Unauthorized:
                            targetfed_id = sql.get_fed_id(fedschat)
                            sql.unsubs_fed(fed_id, targetfed_id)
                            LOGGER.info(
                                "El chat {} anuló la federación {} porque me echaron"
                                .format(fedschat, info['fname']))
                            continue
                    elif excp.message == "User_id_invalid":
                        break
                    else:
                        LOGGER.warning(
                            "No se pudo banear de la federación en {} porque: {}".format(
                                fedschat, excp.message))
                except TelegramError:
                    pass

    if unfbanned_in_chats == 0:
        send_message(update.effective_message,
                     "This person has been un-fbanned in 0 chats.")
    if unfbanned_in_chats > 0:
        send_message(
            update.effective_message,
            "This person has been un-fbanned in {} chats.".format(
                unfbanned_in_chats))
    # Also do not spamming all fed admins
    """
	FEDADMIN = sql.all_fed_users(fed_id)
	for x in FEDADMIN:
		getreport = sql.user_feds_report(x)
		if getreport is False:
			FEDADMIN.remove(x)
	send_to_list(bot, FEDADMIN,
			 "<b>Desbaneo de la Federación</b>" \
			 "\n<b>Federación:</b> {}" \
			 "\n<b>Administrador de la federación:</b> {}" \
			 "\n<b>Usuario:</b> {}" \
			 "\n<b>ID de Usuario:</b> <code>{}</code>".format(info['fname'], mention_html(user.id, user.first_name),
												 mention_html(user_chat.id, user_chat.first_name),
															  user_chat.id),
			html=True)
	"""


@run_async
def set_frules(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == 'private':
        send_message(update.effective_message,
                     "Este comando es específico del grupo, no de nuestro chat privado!")
        return

    fed_id = sql.get_fed_id(chat.id)

    if not fed_id:
        update.effective_message.reply_text(
            "Este grupo no está en ninguna federación!")
        return

    if is_user_fed_admin(fed_id, user.id) is False:
        update.effective_message.reply_text("Solo los administradores de la federación pueden hacer esto!")
        return

    if len(args) >= 1:
        msg = update.effective_message
        raw_text = msg.text
        args = raw_text.split(
            None, 1)  # use python's maxsplit to separate cmd and args
        if len(args) == 2:
            txt = args[1]
            offset = len(txt) - len(
                raw_text)  # set correct offset relative to command
            markdown_rules = markdown_parser(
                txt, entities=msg.parse_entities(), offset=offset)
        x = sql.set_frules(fed_id, markdown_rules)
        if not x:
            update.effective_message.reply_text(
                "Guau! Se produjo un error al establecer las reglas de la federación. Si se pregunta por qué, pregúntelo en @{SUPPORT_CHAT} !"
            )
            return

        rules = sql.get_fed_info(fed_id)['frules']
        getfed = sql.get_fed_info(fed_id)
        get_fedlog = sql.get_fed_log(fed_id)
        if get_fedlog:
            if eval(get_fedlog):
                bot.send_message(
                    get_fedlog,
                    "*{}* ha actualizado las reglas de federación para la federación *{}*".format(
                        user.first_name, getfed['fname']),
                    parse_mode="markdown")
        update.effective_message.reply_text(
            f"Las reglas se han cambiado a :\n{rules}!")
    else:
        update.effective_message.reply_text(
            "Escribe reglas para configurar esto!")


@run_async
def get_frules(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat

    if chat.type == 'private':
        send_message(update.effective_message,
                     "Este comando es específico del grupo, no de nuestro chat privado!")
        return

    fed_id = sql.get_fed_id(chat.id)
    if not fed_id:
        update.effective_message.reply_text(
            "Este grupo no está en ninguna federación!")
        return

    rules = sql.get_frules(fed_id)
    text = "*Reglas en esta federación:*\n"
    text += rules
    update.effective_message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


@run_async
def fed_broadcast(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if chat.type == 'private':
        send_message(update.effective_message,
                     "Este comando es específico del grupo, no de nuestro chat privado!")
        return

    if args:
        chat = update.effective_chat
        fed_id = sql.get_fed_id(chat.id)
        fedinfo = sql.get_fed_info(fed_id)
        if is_user_fed_owner(fed_id, user.id) is False:
            update.effective_message.reply_text(
                "Solo los propietarios de federaciones pueden hacer esto!")
            return
        # Parsing md
        raw_text = msg.text
        args = raw_text.split(
            None, 1)  # use python's maxsplit to separate cmd and args
        txt = args[1]
        offset = len(txt) - len(
            raw_text)  # set correct offset relative to command
        text_parser = markdown_parser(
            txt, entities=msg.parse_entities(), offset=offset)
        text = text_parser
        try:
            broadcaster = user.first_name
        except:
            broadcaster = user.first_name + " " + user.last_name
        text += "\n\n- {}".format(mention_markdown(user.id, broadcaster))
        chat_list = sql.all_fed_chats(fed_id)
        failed = 0
        for chat in chat_list:
            title = "*Nueva transmisión de la Federación {}*\n".format(fedinfo['fname'])
            try:
                bot.sendMessage(chat, title + text, parse_mode="markdown")
            except TelegramError:
                try:
                    dispatcher.bot.getChat(chat)
                except Unauthorized:
                    failed += 1
                    sql.chat_leave_fed(chat)
                    LOGGER.info(
                        "El chat {} abandonó la federación {} porque me echaron".format(
                            chat, fedinfo['fname']))
                    continue
                failed += 1
                LOGGER.warning("No se pudo enviar la transmisión a {}".format(
                    str(chat)))

        send_text = "La transmisión de la federación está completa"
        if failed >= 1:
            send_text += "{} el grupo no pudo recibir el mensaje, probablemente porque abandonó la Federación.".format(
                failed)
        update.effective_message.reply_text(send_text)


@run_async
def fed_ban_list(update: Update, context: CallbackContext):
    bot, args, chat_data = context.bot, context.args, context.chat_data
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == 'private':
        send_message(update.effective_message,
                     "Este comando es específico del grupo, no de nuestro chat privado!")
        return

    fed_id = sql.get_fed_id(chat.id)
    info = sql.get_fed_info(fed_id)

    if not fed_id:
        update.effective_message.reply_text(
            "Este grupo no es parte de ninguna federación!")
        return

    if is_user_fed_owner(fed_id, user.id) is False:
        update.effective_message.reply_text(
            "Solo los propietarios de federaciones pueden hacer esto!")
        return

    user = update.effective_user
    chat = update.effective_chat
    getfban = sql.get_all_fban_users(fed_id)
    if len(getfban) == 0:
        update.effective_message.reply_text(
            "La lista de baneados de la federación de {} está vacía".format(info['fname']),
            parse_mode=ParseMode.HTML)
        return

    if args:
        if args[0] == 'json':
            jam = time.time()
            new_jam = jam + 1800
            cek = get_chat(chat.id, chat_data)
            if cek.get('status'):
                if jam <= int(cek.get('value')):
                    waktu = time.strftime("%H:%M:%S %d/%m/%Y",
                                          time.localtime(cek.get('value')))
                    update.effective_message.reply_text(
                        "Puede hacer una copia de seguridad de sus datos una vez cada 30 minutos!\nPuede hacer una copia de seguridad de nuevo en `{}`"
                        .format(waktu),
                        parse_mode=ParseMode.MARKDOWN)
                    return
                else:
                    if user.id not in DRAGONS:
                        put_chat(chat.id, new_jam, chat_data)
            else:
                if user.id not in DEMONS:
                    put_chat(chat.id, new_jam, chat_data)
            backups = ""
            for users in getfban:
                getuserinfo = sql.get_all_fban_users_target(fed_id, users)
                json_parser = {
                    "user_id": users,
                    "first_name": getuserinfo['first_name'],
                    "last_name": getuserinfo['last_name'],
                    "user_name": getuserinfo['user_name'],
                    "reason": getuserinfo['reason']
                }
                backups += json.dumps(json_parser)
                backups += "\n"
            with BytesIO(str.encode(backups)) as output:
                output.name = "megu_fbanned_users.json"
                update.effective_message.reply_document(
                    document=output,
                    filename="megu_fbanned_users.json",
                    caption="Total {} usuarios baneados por la Federación {}."
                    .format(len(getfban), info['fname']))
            return
        elif args[0] == 'csv':
            jam = time.time()
            new_jam = jam + 1800
            cek = get_chat(chat.id, chat_data)
            if cek.get('status'):
                if jam <= int(cek.get('value')):
                    waktu = time.strftime("%H:%M:%S %d/%m/%Y",
                                          time.localtime(cek.get('value')))
                    update.effective_message.reply_text(
                        "Puede hacer una copia de seguridad de los datos una vez cada 30 minutos!\nPuede hacer una copia de seguridad de nuevo en `{}`"
                        .format(waktu),
                        parse_mode=ParseMode.MARKDOWN)
                    return
                else:
                    if user.id not in DRAGONS:
                        put_chat(chat.id, new_jam, chat_data)
            else:
                if user.id not in DEMONS:
                    put_chat(chat.id, new_jam, chat_data)
            backups = "id,firstname,lastname,username,reason\n"
            for users in getfban:
                getuserinfo = sql.get_all_fban_users_target(fed_id, users)
                backups += "{user_id},{first_name},{last_name},{user_name},{reason}".format(
                    user_id=users,
                    first_name=getuserinfo['first_name'],
                    last_name=getuserinfo['last_name'],
                    user_name=getuserinfo['user_name'],
                    reason=getuserinfo['reason'])
                backups += "\n"
            with BytesIO(str.encode(backups)) as output:
                output.name = "megu_fbanned_users.csv"
                update.effective_message.reply_document(
                    document=output,
                    filename="megu_fbanned_users.csv",
                    caption="Total {} User are blocked by Federation {}."
                    .format(len(getfban), info['fname']))
            return

    text = "<b>{} los usuarios han sido baneados de la federación {}:</b>\n".format(
        len(getfban), info['fname'])
    for users in getfban:
        getuserinfo = sql.get_all_fban_users_target(fed_id, users)
        if getuserinfo is False:
            text = "No hay usuarios baneados de la federación {}".format(
                info['fname'])
            break
        user_name = getuserinfo['first_name']
        if getuserinfo['last_name']:
            user_name += " " + getuserinfo['last_name']
        text += " • {} (<code>{}</code>)\n".format(
            mention_html(users, user_name), users)

    try:
        update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)
    except:
        jam = time.time()
        new_jam = jam + 1800
        cek = get_chat(chat.id, chat_data)
        if cek.get('status'):
            if jam <= int(cek.get('value')):
                waktu = time.strftime("%H:%M:%S %d/%m/%Y",
                                      time.localtime(cek.get('value')))
                update.effective_message.reply_text(
                    "Puede hacer una copia de seguridad de sus datos una vez cada 30 minutos!\nPuede hacer una copia de seguridad de nuevo en `{}`"
                    .format(waktu),
                    parse_mode=ParseMode.MARKDOWN)
                return
            else:
                if user.id not in DRAGONS:
                    put_chat(chat.id, new_jam, chat_data)
        else:
            if user.id not in DEMONS:
                put_chat(chat.id, new_jam, chat_data)
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', text)
        with BytesIO(str.encode(cleantext)) as output:
            output.name = "fbanlist.txt"
            update.effective_message.reply_document(
                document=output,
                filename="fbanlist.txt",
                caption="La siguiente es una lista de usuarios que actualmente están prohibidos en la Federación {}."
                .format(info['fname']))


@run_async
def fed_notif(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    fed_id = sql.get_fed_id(chat.id)

    if not fed_id:
        update.effective_message.reply_text(
            "Este grupo no es parte de ninguna federación!")
        return

    if args:
        if args[0] in ("yes", "on"):
            sql.set_feds_setting(user.id, True)
            msg.reply_text(
                "¡Federación de informes de respaldo! Cada usuario que sea fban/unban se le notificará por privado."
            )
        elif args[0] in ("no", "off"):
            sql.set_feds_setting(user.id, False)
            msg.reply_text(
                "La Federación de Reportes se ha detenido! Cada usuario que sea fban/unban no será notificado por privado."
            )
        else:
            msg.reply_text("Por favor escribe `on`/`off`", parse_mode="markdown")
    else:
        getreport = sql.user_feds_report(user.id)
        msg.reply_text(
            "Sus preferencias actuales de informes de la Federación: `{}`".format(
                getreport),
            parse_mode="markdown")


@run_async
def fed_chats(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == 'private':
        send_message(update.effective_message,
                     "Este comando es específico del grupo, no de nuestro chat privado!")
        return

    fed_id = sql.get_fed_id(chat.id)
    info = sql.get_fed_info(fed_id)

    if not fed_id:
        update.effective_message.reply_text(
            "Este grupo no es parte de ninguna federación!")
        return

    if is_user_fed_admin(fed_id, user.id) is False:
        update.effective_message.reply_text(
            "Solo los administradores de la federación pueden hacer esto!")
        return

    getlist = sql.all_fed_chats(fed_id)
    if len(getlist) == 0:
        update.effective_message.reply_text(
            "Ningún usuario está baneado en la federación {}".format(info['fname']),
            parse_mode=ParseMode.HTML)
        return

    text = "<b>Nuevo chat se unió a la federación {}:</b>\n".format(info['fname'])
    for chats in getlist:
        try:
            chat_name = dispatcher.bot.getChat(chats).title
        except Unauthorized:
            sql.chat_leave_fed(chats)
            LOGGER.info("El chat {} ha abandonado la federación {} porque me echaron".format(
                chats, info['fname']))
            continue
        text += " • {} (<code>{}</code>)\n".format(chat_name, chats)

    try:
        update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)
    except:
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', text)
        with BytesIO(str.encode(cleantext)) as output:
            output.name = "fedchats.txt"
            update.effective_message.reply_document(
                document=output,
                filename="fedchats.txt",
                caption="Aquí hay una lista de todos los chats que se unieron a la federación {}."
                .format(info['fname']))


@run_async
def fed_import_bans(update: Update, context: CallbackContext):
    bot, chat_data = context.bot, context.chat_data
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    if chat.type == 'private':
        send_message(update.effective_message,
                     "Este comando es específico del grupo, no de nuestro chat privado!")
        return

    fed_id = sql.get_fed_id(chat.id)
    info = sql.get_fed_info(fed_id)
    getfed = sql.get_fed_info(fed_id)

    if not fed_id:
        update.effective_message.reply_text(
            "Este grupo no es parte de ninguna federación!")
        return

    if is_user_fed_owner(fed_id, user.id) is False:
        update.effective_message.reply_text(
            "Solo los propietarios de federaciones pueden hacer esto!")
        return

    if msg.reply_to_message and msg.reply_to_message.document:
        jam = time.time()
        new_jam = jam + 1800
        cek = get_chat(chat.id, chat_data)
        if cek.get('status'):
            if jam <= int(cek.get('value')):
                waktu = time.strftime("%H:%M:%S %d/%m/%Y",
                                      time.localtime(cek.get('value')))
                update.effective_message.reply_text(
                    "Puede obtener sus datos una vez cada 30 minutos!\nPuede obtener datos nuevamente en `{}`"
                    .format(waktu),
                    parse_mode=ParseMode.MARKDOWN)
                return
            else:
                if user.id not in DRAGONS:
                    put_chat(chat.id, new_jam, chat_data)
        else:
            if user.id not in DEMONS:
                put_chat(chat.id, new_jam, chat_data)
        #if int(int(msg.reply_to_message.document.file_size)/1024) >= 200:
        #	msg.reply_text("This file is too big!")
        #	return
        success = 0
        failed = 0
        try:
            file_info = bot.get_file(msg.reply_to_message.document.file_id)
        except BadRequest:
            msg.reply_text(
                "Intente descargar y volver a cargar el archivo, este parece roto!"
            )
            return
        fileformat = msg.reply_to_message.document.file_name.split('.')[-1]
        if fileformat == 'json':
            multi_fed_id = []
            multi_import_userid = []
            multi_import_firstname = []
            multi_import_lastname = []
            multi_import_username = []
            multi_import_reason = []
            with BytesIO() as file:
                file_info.download(out=file)
                file.seek(0)
                reading = file.read().decode('UTF-8')
                splitting = reading.split('\n')
                for x in splitting:
                    if x == '':
                        continue
                    try:
                        data = json.loads(x)
                    except json.decoder.JSONDecodeError as err:
                        failed += 1
                        continue
                    try:
                        import_userid = int(data['user_id'])  # Make sure it int
                        import_firstname = str(data['first_name'])
                        import_lastname = str(data['last_name'])
                        import_username = str(data['user_name'])
                        import_reason = str(data['reason'])
                    except ValueError:
                        failed += 1
                        continue
                    # Checking user
                    if int(import_userid) == bot.id:
                        failed += 1
                        continue
                    if is_user_fed_owner(fed_id, import_userid) is True:
                        failed += 1
                        continue
                    if is_user_fed_admin(fed_id, import_userid) is True:
                        failed += 1
                        continue
                    if str(import_userid) == str(OWNER_ID):
                        failed += 1
                        continue
                    if int(import_userid) in DRAGONS:
                        failed += 1
                        continue
                    if int(import_userid) in DEV_USERS:
                        failed += 1
                        continue
                    if int(import_userid) in DEMONS:
                        failed += 1
                        continue
                    if int(import_userid) in TIGERS:
                        failed += 1
                        continue
                    if int(import_userid) in WOLVES:
                        failed += 1
                        continue
                    multi_fed_id.append(fed_id)
                    multi_import_userid.append(str(import_userid))
                    multi_import_firstname.append(import_firstname)
                    multi_import_lastname.append(import_lastname)
                    multi_import_username.append(import_username)
                    multi_import_reason.append(import_reason)
                    success += 1
                sql.multi_fban_user(multi_fed_id, multi_import_userid,
                                    multi_import_firstname,
                                    multi_import_lastname,
                                    multi_import_username, multi_import_reason)
            text = "Los bloques se importaron correctamente. {} personas están bloqueadas.".format(
                success)
            if failed >= 1:
                text += " {} Falló al importar.".format(failed)
            get_fedlog = sql.get_fed_log(fed_id)
            if get_fedlog:
                if eval(get_fedlog):
                    teks = "Federación *{}* ha importado datos correctamente. {} bloqueados.".format(
                        getfed['fname'], success)
                    if failed >= 1:
                        teks += " {} Falló al importar.".format(failed)
                    bot.send_message(get_fedlog, teks, parse_mode="markdown")
        elif fileformat == 'csv':
            multi_fed_id = []
            multi_import_userid = []
            multi_import_firstname = []
            multi_import_lastname = []
            multi_import_username = []
            multi_import_reason = []
            file_info.download("fban_{}.csv".format(
                msg.reply_to_message.document.file_id))
            with open(
                    "fban_{}.csv".format(msg.reply_to_message.document.file_id),
                    'r',
                    encoding="utf8") as csvFile:
                reader = csv.reader(csvFile)
                for data in reader:
                    try:
                        import_userid = int(data[0])  # Make sure it int
                        import_firstname = str(data[1])
                        import_lastname = str(data[2])
                        import_username = str(data[3])
                        import_reason = str(data[4])
                    except ValueError:
                        failed += 1
                        continue
                    # Checking user
                    if int(import_userid) == bot.id:
                        failed += 1
                        continue
                    if is_user_fed_owner(fed_id, import_userid) is True:
                        failed += 1
                        continue
                    if is_user_fed_admin(fed_id, import_userid) is True:
                        failed += 1
                        continue
                    if str(import_userid) == str(OWNER_ID):
                        failed += 1
                        continue
                    if int(import_userid) in DRAGONS:
                        failed += 1
                        continue
                    if int(import_userid) in DEV_USERS:
                        failed += 1
                        continue
                    if int(import_userid) in DEMONS:
                        failed += 1
                        continue
                    if int(import_userid) in TIGERS:
                        failed += 1
                        continue
                    if int(import_userid) in WOLVES:
                        failed += 1
                        continue
                    multi_fed_id.append(fed_id)
                    multi_import_userid.append(str(import_userid))
                    multi_import_firstname.append(import_firstname)
                    multi_import_lastname.append(import_lastname)
                    multi_import_username.append(import_username)
                    multi_import_reason.append(import_reason)
                    success += 1
                    # t = ThreadWithReturnValue(target=sql.fban_user, args=(fed_id, str(import_userid), import_firstname, import_lastname, import_username, import_reason,))
                    # t.start()
                sql.multi_fban_user(multi_fed_id, multi_import_userid,
                                    multi_import_firstname,
                                    multi_import_lastname,
                                    multi_import_username, multi_import_reason)
            csvFile.close()
            os.remove("fban_{}.csv".format(
                msg.reply_to_message.document.file_id))
            text = "Los archivos se importaron correctamente. {} personas bloqueadas.".format(
                success)
            if failed >= 1:
                text += " {} Falló al importar.".format(failed)
            get_fedlog = sql.get_fed_log(fed_id)
            if get_fedlog:
                if eval(get_fedlog):
                    teks = "Federación *{}* ha importado datos correctamente. {} bloqueados.".format(
                        getfed['fname'], success)
                    if failed >= 1:
                        teks += " {} Falló al importar.".format(failed)
                    bot.send_message(get_fedlog, teks, parse_mode="markdown")
        else:
            send_message(update.effective_message,
                         "Este archivo no es compatible.")
            return
        send_message(update.effective_message, text)


@run_async
def del_fed_button(update: Update, context: CallbackContext):
    query = update.callback_query
    userid = query.message.chat.id
    fed_id = query.data.split("_")[1]

    if fed_id == 'cancel':
        query.message.edit_text("Eliminación de la federación cancelada")
        return

    getfed = sql.get_fed_info(fed_id)
    if getfed:
        delete = sql.del_fed(fed_id)
        if delete:
            query.message.edit_text(
                "¡Has eliminado tu Federación! Ahora todos los Grupos que están conectados con `{}` no tienen una Federación."
                .format(getfed['fname']),
                parse_mode='markdown')


@run_async
def fed_stat_user(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    if args:
        if args[0].isdigit():
            user_id = args[0]
        else:
            user_id = extract_user(msg, args)
    else:
        user_id = extract_user(msg, args)

    if user_id:
        if len(args) == 2 and args[0].isdigit():
            fed_id = args[1]
            user_name, reason, fbantime = sql.get_user_fban(
                fed_id, str(user_id))
            if fbantime:
                fbantime = time.strftime("%d/%m/%Y", time.localtime(fbantime))
            else:
                fbantime = "Unavaiable"
            if user_name is False:
                send_message(
                    update.effective_message,
                    "Federación {} no encontrada!".format(fed_id),
                    parse_mode="markdown")
                return
            if user_name == "" or user_name is None:
                user_name = "He/she"
            if not reason:
                send_message(
                    update.effective_message,
                    "{} no está prohibido en esta federación!".format(user_name))
            else:
                teks = "{} baneado en esta federación porque:\n`{}`\n*Baneado en:* `{}`".format(
                    user_name, reason, fbantime)
                send_message(
                    update.effective_message, teks, parse_mode="markdown")
            return
        user_name, fbanlist = sql.get_user_fbanlist(str(user_id))
        if user_name == "":
            try:
                user_name = bot.get_chat(user_id).first_name
            except BadRequest:
                user_name = "He/she"
            if user_name == "" or user_name is None:
                user_name = "He/she"
        if len(fbanlist) == 0:
            send_message(
                update.effective_message,
                "{} no está prohibido en ninguna federación!".format(user_name))
            return
        else:
            teks = "{} ha sido baneado en esta federación:\n".format(user_name)
            for x in fbanlist:
                teks += "- `{}`: {}\n".format(x[0], x[1][:20])
            teks += "\nSi desea obtener más información sobre las razones de ban de la federación específicamente, utilice /fbanstat <FedID>"
            send_message(update.effective_message, teks, parse_mode="markdown")

    elif not msg.reply_to_message and not args:
        user_id = msg.from_user.id
        user_name, fbanlist = sql.get_user_fbanlist(user_id)
        if user_name == "":
            user_name = msg.from_user.first_name
        if len(fbanlist) == 0:
            send_message(
                update.effective_message,
                "{} no está baneado en ninguna federación!".format(user_name))
        else:
            teks = "{} ha sido baneado en esta federación:\n".format(user_name)
            for x in fbanlist:
                teks += "- `{}`: {}\n".format(x[0], x[1][:20])
            teks += "\nSi desea obtener más información sobre las razones de ban de la federación específicamente, utilice /fbanstat <FedID>"
            send_message(update.effective_message, teks, parse_mode="markdown")

    else:
        fed_id = args[0]
        fedinfo = sql.get_fed_info(fed_id)
        if not fedinfo:
            send_message(update.effective_message,
                         "Federación {} no encontrada!".format(fed_id))
            return
        name, reason, fbantime = sql.get_user_fban(fed_id, msg.from_user.id)
        if fbantime:
            fbantime = time.strftime("%d/%m/%Y", time.localtime(fbantime))
        else:
            fbantime = "Unavaiable"
        if not name:
            name = msg.from_user.first_name
        if not reason:
            send_message(update.effective_message,
                         "{} no está baneado en esta federación".format(name))
            return
        send_message(
            update.effective_message,
            "{} baneado en esta federación porque:\n`{}`\n*Banned at:* `{}`"
            .format(name, reason, fbantime),
            parse_mode="markdown")


@run_async
def set_fed_log(update: Update, context: CallbackContext):
    args = context.args
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    if chat.type == 'private':
        send_message(update.effective_message,
                     "Este comando es específico del grupo, no de nuestro chat privado!")
        return

    if args:
        fedinfo = sql.get_fed_info(args[0])
        if not fedinfo:
            send_message(update.effective_message,
                         "Esta Federación no existe!")
            return
        isowner = is_user_fed_owner(args[0], user.id)
        if not isowner:
            send_message(update.effective_message,
                         "Solo el creador de la federación puede establecer registros de la federación.")
            return
        setlog = sql.set_fed_log(args[0], chat.id)
        if setlog:
            send_message(
                update.effective_message,
                "El registro de federación `{}` se ha configurado en {}".format(
                    fedinfo['fname'], chat.title),
                parse_mode="markdown")
    else:
        send_message(update.effective_message,
                     "No ha proporcionado ID de la federación!")


@run_async
def unset_fed_log(update: Update, context: CallbackContext):
    args = context.args
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    if chat.type == 'private':
        send_message(update.effective_message,
                     "Este comando es específico del grupo, no de nuestro chat privado!")
        return

    if args:
        fedinfo = sql.get_fed_info(args[0])
        if not fedinfo:
            send_message(update.effective_message,
                         "Esta Federación no existe!")
            return
        isowner = is_user_fed_owner(args[0], user.id)
        if not isowner:
            send_message(update.effective_message,
                         "Solo el creador de la federación puede establecer registros de la federación.")
            return
        setlog = sql.set_fed_log(args[0], None)
        if setlog:
            send_message(
                update.effective_message,
                "El registro de la federación `{}` se revocó el {}".format(
                    fedinfo['fname'], chat.title),
                parse_mode="markdown")
    else:
        send_message(update.effective_message,
                     "No ha proporcionado ID de la federación!")


@run_async
def subs_feds(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    if chat.type == 'private':
        send_message(update.effective_message,
                     "Este comando es específico del grupo, no de nuestro chat privado!")
        return

    fed_id = sql.get_fed_id(chat.id)
    fedinfo = sql.get_fed_info(fed_id)

    if not fed_id:
        send_message(update.effective_message,
                     "Este grupo no está en ninguna federación!")
        return

    if is_user_fed_owner(fed_id, user.id) is False:
        send_message(update.effective_message, "Solo el propietario de la federación puede hacer esto")
        return

    if args:
        getfed = sql.search_fed_by_id(args[0])
        if getfed is False:
            send_message(update.effective_message,
                         "Ingrese una identificación de federación válida.")
            return
        subfed = sql.subs_fed(args[0], fed_id)
        if subfed:
            send_message(
                update.effective_message,
                "La federación `{}` se ha suscrito la federación `{}`. Cada vez que haya un Fedban de esa federación, esta federación también prohibirá a ese usuario."
                .format(fedinfo['fname'], getfed['fname']),
                parse_mode="markdown")
            get_fedlog = sql.get_fed_log(args[0])
            if get_fedlog:
                if int(get_fedlog) != int(chat.id):
                    bot.send_message(
                        get_fedlog,
                        "La federación `{}` se ha suscrito a la federación `{}`"
                        .format(fedinfo['fname'], getfed['fname']),
                        parse_mode="markdown")
        else:
            send_message(
                update.effective_message,
                "La federación `{}` se suscribio a la federación `{}`.".format(
                    fedinfo['fname'], getfed['fname']),
                parse_mode="markdown")
    else:
        send_message(update.effective_message,
                     "No ha proporcionado ID de la federación!")


@run_async
def unsubs_feds(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    if chat.type == 'private':
        send_message(update.effective_message,
                     "Este comando es específico del grupo, no de nuestro chat privado!")
        return

    fed_id = sql.get_fed_id(chat.id)
    fedinfo = sql.get_fed_info(fed_id)

    if not fed_id:
        send_message(update.effective_message,
                     "Este grupo no está en ninguna federación!")
        return

    if is_user_fed_owner(fed_id, user.id) is False:
        send_message(update.effective_message, "Solo el propietario de la federación puede hacer esto")
        return

    if args:
        getfed = sql.search_fed_by_id(args[0])
        if getfed is False:
            send_message(update.effective_message,
                         "Ingrese una identificación de federación válida.")
            return
        subfed = sql.unsubs_fed(args[0], fed_id)
        if subfed:
            send_message(
                update.effective_message,
                "Federación `{}` ahora cancela la suscripción de la federación `{}`.".format(
                    fedinfo['fname'], getfed['fname']),
                parse_mode="markdown")
            get_fedlog = sql.get_fed_log(args[0])
            if get_fedlog:
                if int(get_fedlog) != int(chat.id):
                    bot.send_message(
                        get_fedlog,
                        "La federación `{}` ha cancelado la suscripción a la federación `{}`.".format(
                            fedinfo['fname'], getfed['fname']),
                        parse_mode="markdown")
        else:
            send_message(
                update.effective_message,
                "Federación `{}` no se está suscribiendo `{}`.".format(
                    fedinfo['fname'], getfed['fname']),
                parse_mode="markdown")
    else:
        send_message(update.effective_message,
                     "No ha proporcionado ID de la federación!")


@run_async
def get_myfedsubs(update: Update, context: CallbackContext):
    args = context.args
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    if chat.type == 'private':
        send_message(update.effective_message,
                     "Este comando es específico del grupo, no de nuestro chat privado!")
        return

    fed_id = sql.get_fed_id(chat.id)
    fedinfo = sql.get_fed_info(fed_id)

    if not fed_id:
        send_message(update.effective_message,
                     "Este grupo no está en ninguna federación!")
        return

    if is_user_fed_owner(fed_id, user.id) is False:
        send_message(update.effective_message, "Solo el propietario de la federación puede hacer esto")
        return

    try:
        getmy = sql.get_mysubs(fed_id)
    except:
        getmy = []

    if len(getmy) == 0:
        send_message(
            update.effective_message,
            "La federación `{}` no se está suscribiendo a ninguna federación.".format(
                fedinfo['fname']),
            parse_mode="markdown")
        return
    else:
        listfed = "La federación `{}` se suscribe a la federación:\n".format(
            fedinfo['fname'])
        for x in getmy:
            listfed += "- `{}`\n".format(x)
        listfed += "\nPara recibir información `/fedinfo <fedid>`. Para darse de baja `/unsubfed <fedid>`."
        send_message(update.effective_message, listfed, parse_mode="markdown")


@run_async
def get_myfeds_list(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    fedowner = sql.get_user_owner_fed_full(user.id)
    if fedowner:
        text = "*Eres dueño de las federaciónes:\n*"
        for f in fedowner:
            text += "- `{}`: *{}*\n".format(f['fed_id'], f['fed']['fname'])
    else:
        text = "*No tienes federaciónes!*"
    send_message(update.effective_message, text, parse_mode="markdown")


def is_user_fed_admin(fed_id, user_id):
    fed_admins = sql.all_fed_users(fed_id)
    if fed_admins is False:
        return False
    if int(user_id) in fed_admins or int(user_id) == OWNER_ID:
        return True
    else:
        return False


def is_user_fed_owner(fed_id, user_id):
    getsql = sql.get_fed_info(fed_id)
    if getsql is False:
        return False
    getfedowner = eval(getsql['fusers'])
    if getfedowner is None or getfedowner is False:
        return False
    getfedowner = getfedowner['owner']
    if str(user_id) == getfedowner or int(user_id) == OWNER_ID:
        return True
    else:
        return False


# There's no handler for this yet, but updating for v12 in case its used
@run_async
def welcome_fed(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    fed_id = sql.get_fed_id(chat.id)
    fban, fbanreason, fbantime = sql.get_fban_user(fed_id, user.id)
    if fban:
        update.effective_message.reply_text(
            "Este usuario está baneado en la federación actual! Lo quitaré.")
        bot.kick_chat_member(chat.id, user.id)
        return True
    else:
        return False


def __stats__():
    all_fbanned = sql.get_all_fban_users_global()
    all_feds = sql.get_all_feds_users_global()
    return "{} usuarios prohibidos en {} Federaciones".format(
        len(all_fbanned), len(all_feds))


def __user_info__(user_id, chat_id):
    fed_id = sql.get_fed_id(chat_id)
    if fed_id:
        fban, fbanreason, fbantime = sql.get_fban_user(fed_id, user_id)
        info = sql.get_fed_info(fed_id)
        infoname = info['fname']

        if int(info['owner']) == user_id:
            text = "Propietario de la federación: <b>{}</b>.".format(infoname)
        elif is_user_fed_admin(fed_id, user_id):
            text = "Administrador de la federación: <b>{}</b>.".format(infoname)

        elif fban:
            text = "Baneado de la Federación: <b>Si</b>"
            text += "\n<b>Razón:</b> {}".format(fbanreason)
        else:
            text = "Baneado de la Federación: <b>No</b>"
    else:
        text = ""
    return text


# Temporary data
def put_chat(chat_id, value, chat_data):
    # print(chat_data)
    if value is False:
        status = False
    else:
        status = True
    chat_data[chat_id] = {'federation': {"status": status, "value": value}}


def get_chat(chat_id, chat_data):
    # print(chat_data)
    try:
        value = chat_data[chat_id]['federation']
        return value
    except KeyError:
        return {"status": False, "value": False}


@run_async
def fed_owner_help(update: Update, context: CallbackContext):
    update.effective_message.reply_text(
        """* 👑 Solo propietario de la Fed: *
 •`/newfed <fed_name>`*:* Crea una Federación, una permitida por usuario. También se puede utilizar para cambiar el nombre de la Federación.máx.64 caracteres)
 •`/delfed <fed_id>`*:* Elimina una Federación y cualquier información relacionada con ella. No cancelará usuarios bloqueados.
 •`/fpromote <usuario>`*:* Asigna al usuario como administrador de la federación. Habilita todos los comandos para el usuario en "Admins de la Federación".
 •`/fdemote <usuario>`*:* Elimina al Usuario de la Federación de administración a un Usuario normal.
 •`/subfed <fed_id>`*:* Se suscribe a un ID de feed dado, las prohibiciones de ese feed suscrito también se producirán en tu feed.
 •`/unsubfed <fed_id>`*:* Anula la suscripción a un ID de feed determinado.
 •`/setfedlog <fed_id>`*:* Establece el canal como base de informes de registro de datos para la federación.
 •`/unsetfedlog <fed_id>`*:* Elimina el canal de base de informes de registro de datos para la federación.
 •`/fbroadcast <message>`*:* Transmite un mensaje a todos los grupos que se han unido a su feed.
 •`/fedsubs` *: * Muestra los federales a los que está suscrito su grupo. `(rn roto)`""",
        parse_mode=ParseMode.MARKDOWN)


@run_async
def fed_admin_help(update: Update, context: CallbackContext):
    update.effective_message.reply_text(
        """*  Administradores de la Federacion: *
  • `/fban <usuario> <motivo>`*:* Banea a un usuario de la federación.
  • `/funban <usuario> <razón>`*:* Desbanea a un usuario de la federación.
  • `/fedinfo <fed_id>`*:* Información sobre la Federación especificada.
  • `/joinfed <fed_id>`*:* Únirse al chat actual de la Federación. Solo los propietarios de los grupos pueden hacer esto. Cada grupo solo puede estar en una Federación.
  • `/leavefed <fed_id>`*:* Deja la Federación dada. Solo los propietarios de los grupos pueden hacer esto.
  • `/setfrules <rules>`*:* Organizar las reglas de la Federación.
  • `/fednotif <on/off>`*:* La configuración de la federación no está en PM cuando hay usuarios que están baneados/desbaneados de la federación.
  • `/frules`*:* Ver reglamento de la Federación.
  • `/fedadmins`*:* Mostrar administrador de la Federación.
  • `/fbanlist`*:* Muestra todos los usuarios que son victimizados en la Federación en este momento.
  • `/fedchats`*:* Obten todos los chats que están conectados en la Federación.\n""",
        parse_mode=ParseMode.MARKDOWN)


@run_async
def fed_user_help(update: Update, context: CallbackContext):
    update.effective_message.reply_text(
        """*Cualquier usuario:*
•`/fbanstat`*:* Muestra si usted o el usuario al que está respondiendo o su nombre de usuario está prohibido en algún lugar o no.
•`/chatfed`*:* Ver la Federación en el chat actual.\n""",
        parse_mode=ParseMode.MARKDOWN)


__mod_name__ = "Federations"


NEW_FED_HANDLER = CommandHandler("newfed", new_fed)
DEL_FED_HANDLER = CommandHandler("delfed", del_fed)
JOIN_FED_HANDLER = CommandHandler("joinfed", join_fed)
LEAVE_FED_HANDLER = CommandHandler("leavefed", leave_fed)
PROMOTE_FED_HANDLER = CommandHandler("fpromote", user_join_fed)
DEMOTE_FED_HANDLER = CommandHandler("fdemote", user_demote_fed)
INFO_FED_HANDLER = CommandHandler("fedinfo", fed_info)
BAN_FED_HANDLER = DisableAbleCommandHandler("fban", fed_ban)
UN_BAN_FED_HANDLER = CommandHandler("unfban", unfban)
FED_BROADCAST_HANDLER = CommandHandler("fbroadcast", fed_broadcast)
FED_SET_RULES_HANDLER = CommandHandler("setfrules", set_frules)
FED_GET_RULES_HANDLER = CommandHandler("frules", get_frules)
FED_CHAT_HANDLER = CommandHandler("chatfed", fed_chat)
FED_ADMIN_HANDLER = CommandHandler("fedadmins", fed_admin)
FED_USERBAN_HANDLER = CommandHandler("fbanlist", fed_ban_list)
FED_NOTIF_HANDLER = CommandHandler("fednotif", fed_notif)
FED_CHATLIST_HANDLER = CommandHandler("fedchats", fed_chats)
FED_IMPORTBAN_HANDLER = CommandHandler("importfbans", fed_import_bans)
FEDSTAT_USER = DisableAbleCommandHandler(["fedstat", "fbanstat"], fed_stat_user)
SET_FED_LOG = CommandHandler("setfedlog", set_fed_log)
UNSET_FED_LOG = CommandHandler("unsetfedlog", unset_fed_log)
SUBS_FED = CommandHandler("subfed", subs_feds)
UNSUBS_FED = CommandHandler("unsubfed", unsubs_feds)
MY_SUB_FED = CommandHandler("fedsubs", get_myfedsubs)
MY_FEDS_LIST = CommandHandler("myfeds", get_myfeds_list)
DELETEBTN_FED_HANDLER = CallbackQueryHandler(del_fed_button, pattern=r"rmfed_")
FED_OWNER_HELP_HANDLER = CommandHandler("fedownerhelp", fed_owner_help)
FED_ADMIN_HELP_HANDLER = CommandHandler("fedadminhelp", fed_admin_help)
FED_USER_HELP_HANDLER = CommandHandler("feduserhelp", fed_user_help)

dispatcher.add_handler(NEW_FED_HANDLER)
dispatcher.add_handler(DEL_FED_HANDLER)
dispatcher.add_handler(JOIN_FED_HANDLER)
dispatcher.add_handler(LEAVE_FED_HANDLER)
dispatcher.add_handler(PROMOTE_FED_HANDLER)
dispatcher.add_handler(DEMOTE_FED_HANDLER)
dispatcher.add_handler(INFO_FED_HANDLER)
dispatcher.add_handler(BAN_FED_HANDLER)
dispatcher.add_handler(UN_BAN_FED_HANDLER)
dispatcher.add_handler(FED_BROADCAST_HANDLER)
dispatcher.add_handler(FED_SET_RULES_HANDLER)
dispatcher.add_handler(FED_GET_RULES_HANDLER)
dispatcher.add_handler(FED_CHAT_HANDLER)
dispatcher.add_handler(FED_ADMIN_HANDLER)
dispatcher.add_handler(FED_USERBAN_HANDLER)
dispatcher.add_handler(FED_NOTIF_HANDLER)
dispatcher.add_handler(FED_CHATLIST_HANDLER)
#dispatcher.add_handler(FED_IMPORTBAN_HANDLER)
dispatcher.add_handler(FEDSTAT_USER)
dispatcher.add_handler(SET_FED_LOG)
dispatcher.add_handler(UNSET_FED_LOG)
dispatcher.add_handler(SUBS_FED)
dispatcher.add_handler(UNSUBS_FED)
dispatcher.add_handler(MY_SUB_FED)
dispatcher.add_handler(MY_FEDS_LIST)
dispatcher.add_handler(DELETEBTN_FED_HANDLER)
dispatcher.add_handler(FED_OWNER_HELP_HANDLER)
dispatcher.add_handler(FED_ADMIN_HELP_HANDLER)
dispatcher.add_handler(FED_USER_HELP_HANDLER)
