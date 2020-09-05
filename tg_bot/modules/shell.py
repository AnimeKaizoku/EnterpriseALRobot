# Shell command executor
# Written by t.me/Zero_cool7870 and t.me/TheRealPhoenix

from tg_bot import dispatcher, LOGGER
from telegram import Bot, Update
from telegram.ext.dispatcher import run_async
from tg_bot.modules.helper_funcs.chat_status import dev_plus
from tg_bot.modules.helper_funcs.misc import sendMessage
from telegram.ext import CommandHandler
from subprocess import Popen, PIPE


def shell(command):
    process = Popen(command, stdout=PIPE, shell=True, stderr=PIPE)
    stdout, stderr = process.communicate()
    return (stdout, stderr)


@dev_plus
@run_async
def shellExecute(bot: Bot, update: Update):
    cmd = update.message.text.split(" ", maxsplit=1)
    if len(cmd) == 1:
        sendMessage("No command provided!", bot, update)
        return
    LOGGER.info(cmd)
    output = shell(cmd[1])
    if output[1].decode():
        LOGGER.error(f"Shell: {output[1].decode()}")
    if len(output[0].decode()) > 4000:
        with open("shell.txt", "w") as f:
            f.write(f"Output\n-----------\n{output[0].decode()}\n")
            if output[1]:
                f.write(f"STDError\n-----------\n{output[1].decode()}\n")
        with open("shell.txt", "rb") as f:
            bot.send_document(
                document=f,
                filename=f.name,
                reply_to_message_id=update.message.message_id,
                chat_id=update.message.chat_id,
            )
    else:
        if output[1].decode():
            sendMessage(f"<code>{output[1].decode()}</code>", bot, update)
            return
        else:
            sendMessage(f"<code>{output[0].decode()}</code>", bot, update)


shell_handler = CommandHandler(("sh", "shell"), shellExecute)
dispatcher.add_handler(shell_handler)