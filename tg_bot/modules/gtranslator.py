from gpytranslate import Translator
import asyncio
from tg_bot import kp
from pyrogram import filters


@kp.on_message(filters.command(["tr", "tl"], prefixes=["/", "!", "."]))
async def translate(_client, message):
    trl = Translator()
    if message.reply_to_message and (
        message.reply_to_message.text or message.reply_to_message.caption
    ):
        if len(message.text.split()) == 1:
            await message.reply_text(
                "Provide lang code.\n[Available options](https://telegra.ph/Lang-Codes-11-08).\n**Usage:** `/tr en`"
            )
            return
        target = message.text.split()[1]
        if message.reply_to_message.text:
            text = message.reply_to_message.text
        else:
            text = message.reply_to_message.caption
        detectlang = await trl.detect(text)
        try:
            tekstr = await trl(text, targetlang=target)
        except ValueError as err:
            await message.reply_text(f"Error: `{str(err)}`")
            return
    else:
        if len(message.text.split()) <= 2:
            await message.reply_text(
                "Provide lang code.\n[Available options](https://telegra.ph/Lang-Codes-11-08).\n**Usage:** `/tr en`"
            )
            return
        target = message.text.split(None, 2)[1]
        text = message.text.split(None, 2)[2]
        detectlang = await trl.detect(text)
        try:
            tekstr = await trl(text, targetlang=target)
        except ValueError as err:
            await message.reply_text("Error: `{}`".format(str(err)))
            return

    await message.reply_text(f"**Translated:**\n```{tekstr.text}```")


if __name__ == "__translate__":
    asyncio.run(translate())

from tg_bot.modules.language import gs

def get_help(chat):
    return gs(chat, "gtranslate_help")


__mod_name__ = "Translator"
__command_list__ = ["tr", "tl"]
