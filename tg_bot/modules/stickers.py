import hashlib
import os
import math
import urllib.request as urllib

from io import BytesIO
from PIL import Image

from typing import Optional, List
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram import TelegramError
from telegram import Update, Bot
from telegram.ext import CommandHandler, run_async
from telegram.utils.helpers import escape_markdown

from tg_bot import dispatcher

from tg_bot.modules.disable import DisableAbleCommandHandler


@run_async
def stickerid(bot: Bot, update: Update):
    msg = update.effective_message
    if msg.reply_to_message and msg.reply_to_message.sticker:
        update.effective_message.reply_text("Sticker ID:\n```" +
                                            escape_markdown(msg.reply_to_message.sticker.file_id) + "```",
                                            parse_mode=ParseMode.MARKDOWN)
    else:
        update.effective_message.reply_text("Please reply to a sticker to get its ID.")


@run_async
def getsticker(bot: Bot, update: Update):
    msg = update.effective_message
    chat_id = update.effective_chat.id
    if msg.reply_to_message and msg.reply_to_message.sticker:
        file_id = msg.reply_to_message.sticker.file_id
        newFile = bot.get_file(file_id)
        newFile.download('sticker.png')
        bot.send_document(chat_id, document=open('sticker.png', 'rb'))
        os.remove("sticker.png")
    else:
        update.effective_message.reply_text("Please reply to a sticker for me to upload its PNG.")


@run_async
def steal(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message
    user = update.effective_user
    packnum = 0
    packname = "a" + str(user.id) + "_by_"+bot.username
    packname_found = 0
    max_stickers = 120
    while packname_found == 0:
        try:
            stickerset = bot.get_sticker_set(packname)
            if len(stickerset.stickers) >= max_stickers:
                    packnum += 1
                    packname = "a" + str(packnum) + "_" + str(user.id) + "_by_"+bot.username
            else:
                packname_found = 1
        except TelegramError as e:
            if e.message == "Stickerset_invalid":
                packname_found = 1
    stolensticker = "stolensticker.png"
    if msg.reply_to_message:
        if msg.reply_to_message.sticker:
            file_id = msg.reply_to_message.sticker.file_id
        elif msg.reply_to_message.photo:
            file_id = msg.reply_to_message.photo[-1].file_id
        elif msg.reply_to_message.document:
            file_id = msg.reply_to_message.document.file_id
        else:
            msg.reply_text("Yea, I can't steal that.")
        stolen_file = bot.get_file(file_id)
        stolen_file.download('stolensticker.png')
        if args:
            sticker_emoji = str(args[0])
        elif msg.reply_to_message.sticker and msg.reply_to_message.sticker.emoji:
            sticker_emoji = msg.reply_to_message.sticker.emoji
        else:
            sticker_emoji = "🤔"
        try:
            im = Image.open(stolensticker)
            maxsize = (512, 512)
            if (im.width and im.height) < 512:
                size1 = im.width
                size2 = im.height
                if im.width > im.height:
                    scale = 512/size1
                    size1new = 512
                    size2new = size2 * scale
                else:
                    scale = 512/size2
                    size1new = size1 * scale
                    size2new = 512
                size1new = math.floor(size1new)
                size2new = math.floor(size2new)
                sizenew = (size1new, size2new)
                im = im.resize(sizenew)
            else:
                im.thumbnail(maxsize)
            if not msg.reply_to_message.sticker:
                im.save(stolensticker, "PNG")
            bot.add_sticker_to_set(user_id=user.id, name=packname,
                                    png_sticker=open('stolensticker.png', 'rb'), emojis=sticker_emoji)
            msg.reply_text(f"Sticker successfully added to [pack](t.me/addstickers/{packname})" +
                            f"\nEmoji is: {sticker_emoji}", parse_mode=ParseMode.MARKDOWN)
        except OSError as e:
            msg.reply_text("I can only steal images, dude.")
            print(e)
            return
        except TelegramError as e:
            if e.message == "Stickerset_invalid":
                makepack_internal(msg, user, open('stolensticker.png', 'rb'), sticker_emoji, bot, packname, packnum)
            elif e.message == "Sticker_png_dimensions":
                im.save(stolensticker, "PNG")
                bot.add_sticker_to_set(user_id=user.id, name=packname,
                                        png_sticker=open('stolensticker.png', 'rb'), emojis=sticker_emoji)
                msg.reply_text(f"Sticker successfully added to [pack](t.me/addstickers/{packname})" +
                                f"\nEmoji is: {sticker_emoji}", parse_mode=ParseMode.MARKDOWN)
            elif e.message == "Invalid sticker emojis":
                msg.reply_text("Invalid emoji(s).")
            elif e.message == "Stickers_too_much":
                msg.reply_text("Max packsize reached.")
            elif e.message == "Internal Server Error: sticker set not found (500)":
                msg.reply_text("Sticker successfully added to [pack](t.me/addstickers/%s)" % packname + "\n"
                            "Emoji is:" + " " + sticker_emoji, parse_mode=ParseMode.MARKDOWN)
            print(e)
    elif args:
        try:
            try:
                urlemoji = msg.text.split(" ")
                png_sticker = urlemoji[1] 
                sticker_emoji = urlemoji[2]
            except IndexError:
                sticker_emoji = "🤔"
            urllib.urlretrieve(png_sticker, stolensticker)
            im = Image.open(stolensticker)
            maxsize = (512, 512)
            if (im.width and im.height) < 512:
                size1 = im.width
                size2 = im.height
                if im.width > im.height:
                    scale = 512/size1
                    size1new = 512
                    size2new = size2 * scale
                else:
                    scale = 512/size2
                    size1new = size1 * scale
                    size2new = 512
                size1new = math.floor(size1new)
                size2new = math.floor(size2new)
                sizenew = (size1new, size2new)
                im = im.resize(sizenew)
            else:
                im.thumbnail(maxsize)
            im.save(stolensticker, "PNG")
            msg.reply_photo(photo=open('stolensticker.png', 'rb'))
            bot.add_sticker_to_set(user_id=user.id, name=packname,
                                    png_sticker=open('stolensticker.png', 'rb'), emojis=sticker_emoji)
            msg.reply_text(f"Sticker successfully added to [pack](t.me/addstickers/{packname})" +
                            f"\nEmoji is: {sticker_emoji}", parse_mode=ParseMode.MARKDOWN)
        except OSError as e:
            msg.reply_text("I can only steal images, dude.")
            print(e)
            return
        except TelegramError as e:
            if e.message == "Stickerset_invalid":
                makepack_internal(msg, user, open('stolensticker.png', 'rb'), sticker_emoji, bot, packname, packnum)
            elif e.message == "Sticker_png_dimensions":
                im.save(stolensticker, "PNG")
                bot.add_sticker_to_set(user_id=user.id, name=packname,
                                        png_sticker=open('stolensticker.png', 'rb'), emojis=sticker_emoji)
                msg.reply_text("Sticker successfully added to [pack](t.me/addstickers/%s)" % packname + "\n" +
                            "Emoji is:" + " " + sticker_emoji, parse_mode=ParseMode.MARKDOWN)
            elif e.message == "Invalid sticker emojis":
                msg.reply_text("Invalid emoji(s).")
            elif e.message == "Stickers_too_much":
                msg.reply_text("Max packsize reached.")
            elif e.message == "Internal Server Error: sticker set not found (500)":
                msg.reply_text("Sticker successfully added to [pack](t.me/addstickers/%s)" % packname + "\n"
                            "Emoji is:" + " " + sticker_emoji, parse_mode=ParseMode.MARKDOWN)
            print(e)
    else:
        packs = "Please reply to a sticker or image to steal it to your pack!\nOh by the way, here are your packs:\n"
        if packnum > 0:
            firstpackname = "a" + str(user.id) + "_by_"+bot.username
            for i in range(0, packnum + 1):
                if i == 0:
                    packs += f"[pack](t.me/addstickers/{firstpackname})\n"
                else:
                    packs += f"[pack{i}](t.me/addstickers/{packname})\n"
        else:
            packs += f"[pack](t.me/addstickers/{packname})"
        msg.reply_text(packs, parse_mode=ParseMode.MARKDOWN)
    if os.path.isfile("stolensticker.png"):
        os.remove("stolensticker.png")


def makepack_internal(msg, user, png_sticker, emoji, bot, packname, packnum):
    name = user.first_name
    name = name[:50]
    try:
        extra_version = ""
        if packnum > 0:
            extra_version = " " + str(packnum)
        success = bot.create_new_sticker_set(user.id, packname, f"{name}'s Sticker Pack" + extra_version,
                                             png_sticker=png_sticker,
                                             emojis=emoji)
    except TelegramError as e:
        print(e)
        if e.message == "Sticker set name is already occupied":
            msg.reply_text("Your pack can be found [here](t.me/addstickers/%s)" % packname,
                           parse_mode=ParseMode.MARKDOWN)
        elif e.message == "Peer_id_invalid":
            msg.reply_text("Contact me in PM first.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
                text="Start", url=f"t.me/{bot.username}")]]))
        elif e.message == "Internal Server Error: created sticker set not found (500)":
                msg.reply_text("Sticker pack successfully created! Get it [here](t.me/addstickers/%s)" % packname,
                       parse_mode=ParseMode.MARKDOWN)
        return

    if success:
        msg.reply_text("Sticker pack successfully created! Get it [here](t.me/addstickers/%s)" % packname,
                       parse_mode=ParseMode.MARKDOWN)
    else:
        msg.reply_text("Failed to create sticker pack.")


STICKERID_HANDLER = DisableAbleCommandHandler("stickerid", stickerid)
GETSTICKER_HANDLER = DisableAbleCommandHandler("getsticker", getsticker)
STEAL_HANDLER = DisableAbleCommandHandler("steal", steal, pass_args=True, admin_ok=False)

dispatcher.add_handler(STICKERID_HANDLER)
dispatcher.add_handler(GETSTICKER_HANDLER)
dispatcher.add_handler(STEAL_HANDLER)
