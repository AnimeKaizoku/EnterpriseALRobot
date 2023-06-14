import html
import random
import time

from telegram import ChatPermissions, ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext, run_async

import tg_bot.modules.fun_strings as fun_strings
from tg_bot import dispatcher
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import is_user_admin
from tg_bot.modules.helper_funcs.extraction import extract_user

GIF_ID = "CgACAgQAAx0CSVUvGgAC7KpfWxMrgGyQs-GUUJgt-TSO8cOIDgACaAgAAlZD0VHT3Zynpr5nGxsE"
ABRAZOS = ( "CgACAgQAAxkBAAIKf2P6CpJVDj0De58JLkpzxFrj3xksAAJDAwACBT8FU0BH0ohPgRP4LgQ",
"CgACAgQAAxkBAAIKZWP6CUZDh3tHWxPQ5uWCs-0vsN88AAL9AgACRwABnFOt4IDvQaRW8i4E",
"CgACAgQAAxkBAAIKZmP6CU5B1w9N4U6fxINefH_S1AABuQACMwMAAgdkJVIBoEVp0L9hrS4E",
"CgACAgQAAxkBAAIKbWP6CbYSoi5Y-13sDPKPNMrlcIx_AAK2AwACoQgtUg8KsyNe-FCQLgQ",
"CgACAgQAAxkBAAIKaWP6CXqwArUjfOavtzlFaTEcmv7mAAI6AwACTm8MU9vkhpbNGrEQLgQ",
"CgACAgQAAxkBAAIKa2P6CaK3HUEQ6VD3Fe6gHuVjfvjZAAKjAgAC2MoVU9QYo9XjuHt8LgQ",
"CgACAgQAAxkBAAIKeGP6CjoihTUJORmRrRcT049Ruk30AAI5AwACW_4FU_KSDvKoMTd_LgQ",
"CgACAgQAAxkBAAIKb2P6Cc-EwECqVkD6hFmyLZEca6z9AAL2AgACcVIkU4cD-1J_iewSLgQ",
"CgACAgQAAxkBAAIKdmP6CfnD10YnlZvQZpbuZsUfpSsqAAKvAgACLfYdU1j6zvOUraBSLgQ",
"CgACAgQAAxkBAAIKe2P6Cl170tbUYnSSAAH5-db3_FiSYwACFQMAAvr_PVNkSSSXBht4jC4E",
"CgACAgQAAxkBAAIKeWP6CkULO4-z2OKM48TAlPhGe4R7AALjAgADzQxTmct9ElPS8mMuBA",
"CgACAgQAAxkBAAIKemP6ClF9eHDP2pWxCz4GmYA8X55mAALyAgACAVIUU4_KQ5kGMtUGLgQ",
"CgACAgQAAxkBAAIKfGP6Cmaq5PBJLoSQ6c6FEo2L2behAAJ1AwAC80ZcUjeRWUsouujzLgQ",
"CgACAgQAAxkBAAIKfWP6Cm1kP7HtPtLYi37wtbWDJzARAALAAgACaXMsUx6AJagJo551LgQ",
"CgACAgQAAxkBAAIKfmP6Coh2r4Xzqcez2rCCQKLtROKyAALgAgACrgABFVMa6IpNBEWjNy4E",
"CgACAgQAAxkBAAIKZ2P6CV0GaD50aZxMkFvriwmghizpAAJVAwACBjZUUQn_Ue6O57DbLgQ",
          )

JUDGES = (
       "Este usuario evidentemente está mintiendo, pinche mentiroso!",
       "Este usuario está diciendo la verdad señores, no sean desconfiados",
       "Mmm... No se, Rick... parece falso...",
       "Mi instinto me dice que este usuario está diciendo la verdad",
)


@run_async
def judge(update: Update, context: CallbackContext):
         update.effective_message.reply_to_message.reply_text(random.choice(JUDGES))

@run_async
def kiss(update: Update, context: CallbackContext):
        user1 = html.escape(update.effective_message.from_user.first_name)
        user2 = html.escape(context.bot.get_chat(extract_user(update.effective_message, context.args)).first_name)

        update.effective_message.reply_to_message.reply_animation(random.choice(fun_strings.KISS_STRINGS), caption=f"{user1} ha besado apasionadamente a {user2} Que bonito es el AMOR💕!!")
     
@run_async
def hug(update: Update, context: CallbackContext):

        user1 = html.escape(update.effective_message.from_user.first_name)
        user2 = html.escape(context.bot.get_chat(extract_user(update.effective_message, context.args)).first_name)
       
        update.effective_message.reply_to_message.reply_animation(random.choice(ABRAZOS), caption=f"Owww 💕 {user1} le ha dado un abrazo a {user2}. Que lindooss!")


@run_async
def runs(update: Update, context: CallbackContext):
    update.effective_message.reply_text(random.choice(fun_strings.RUN_STRINGS))


@run_async
def sanitize(update: Update, context: CallbackContext):
    message = update.effective_message
    name = (
        message.reply_to_message.from_user.first_name
        if message.reply_to_message
        else message.from_user.first_name
    )
    reply_animation = (
        message.reply_to_message.reply_animation
        if message.reply_to_message
        else message.reply_animation
    )
    reply_animation(GIF_ID, caption=f"*Sanitizes {name}*")

    
@run_async
def slap(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    chat = update.effective_chat

    reply_text = (
        message.reply_to_message.reply_text
        if message.reply_to_message
        else message.reply_text
    )

    curr_user = html.escape(message.from_user.first_name)
    user_id = extract_user(message, args)

    if user_id == bot.id:
        temp = random.choice(fun_strings.SLAP_FALLEN_TEMPLATES)

        if isinstance(temp, list):
            if temp[2] == "tmute":
                if is_user_admin(chat, message.from_user.id):
                    reply_text(temp[1])
                    return

                mutetime = int(time.time() + 60)
                bot.restrict_chat_member(
                    chat.id,
                    message.from_user.id,
                    until_date=mutetime,
                    permissions=ChatPermissions(can_send_messages=False),
                )
            reply_text(temp[0])
        else:
            reply_text(temp)
        return

    if user_id:
        slapped_user = bot.get_chat(user_id)
        user1 = curr_user
        user2 = html.escape(slapped_user.first_name)

    else:
        user1 = bot.first_name
        user2 = curr_user

    temp = random.choice(fun_strings.SLAP_TEMPLATES)
    item = random.choice(fun_strings.ITEMS)
    hit = random.choice(fun_strings.HIT)
    throw = random.choice(fun_strings.THROW)

    if update.effective_user.id == 1096215023:
        temp = "@NeoTheKitty scratches {user2}"

    reply = temp.format(user1=user1, user2=user2, item=item, hits=hit, throws=throw)

    reply_text(reply, parse_mode=ParseMode.HTML)


@run_async
def pat(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    message = update.effective_message

    reply_to = message.reply_to_message if message.reply_to_message else message

    curr_user = html.escape(message.from_user.first_name)
    user_id = extract_user(message, args)

    if user_id:
        patted_user = bot.get_chat(user_id)
        user1 = curr_user
        user2 = html.escape(patted_user.first_name)

    else:
        user1 = bot.first_name
        user2 = curr_user

    pat_type = random.choice(("Text", "Gif", "Sticker"))
    if pat_type == "Gif":
        try:
            temp = random.choice(fun_strings.PAT_GIFS)
            reply_to.reply_animation(temp)
        except BadRequest:
            pat_type = "Text"

    if pat_type == "Sticker":
        try:
            temp = random.choice(fun_strings.PAT_STICKERS)
            reply_to.reply_sticker(temp)
        except BadRequest:
            pat_type = "Text"

    if pat_type == "Text":
        temp = random.choice(fun_strings.PAT_TEMPLATES)
        reply = temp.format(user1=user1, user2=user2)
        reply_to.reply_text(reply, parse_mode=ParseMode.HTML)


@run_async
def roll(update: Update, context: CallbackContext):
    update.message.reply_text(random.choice(range(1, 7)))


@run_async
def shout(update: Update, context: CallbackContext):
    args = context.args
    text = " ".join(args)
    result = []
    result.append(" ".join(list(text)))
    for pos, symbol in enumerate(text[1:]):
        result.append(symbol + " " + "  " * pos + symbol)
    result = list("\n".join(result))
    result[0] = text[0]
    result = "".join(result)
    msg = "```\n" + result + "```"
    return update.effective_message.reply_text(msg, parse_mode="MARKDOWN")


@run_async
def toss(update: Update, context: CallbackContext):
    update.message.reply_text(random.choice(fun_strings.TOSS))


@run_async
def shrug(update: Update, context: CallbackContext):
    msg = update.effective_message
    reply_text = (
        msg.reply_to_message.reply_text if msg.reply_to_message else msg.reply_text
    )
    reply_text(r"¯\_(ツ)_/¯")


@run_async
def bluetext(update: Update, context: CallbackContext):
    msg = update.effective_message
    reply_text = (
        msg.reply_to_message.reply_text if msg.reply_to_message else msg.reply_text
    )
    reply_text(
        "/BLUE /TEXT\n/MUST /CLICK\n/I /AM /A /STUPID /ANIMAL /THAT /IS /ATTRACTED /TO /COLORS"
    )


@run_async
def rlg(update: Update, context: CallbackContext):
    eyes = random.choice(fun_strings.EYES)
    mouth = random.choice(fun_strings.MOUTHS)
    ears = random.choice(fun_strings.EARS)

    if len(eyes) == 2:
        repl = ears[0] + eyes[0] + mouth[0] + eyes[1] + ears[1]
    else:
        repl = ears[0] + eyes[0] + mouth[0] + eyes[0] + ears[1]
    update.message.reply_text(repl)


@run_async
def decide(update: Update, context: CallbackContext):
    reply_text = (
        update.effective_message.reply_to_message.reply_text
        if update.effective_message.reply_to_message
        else update.effective_message.reply_text
    )
    reply_text(random.choice(fun_strings.DECIDE))


@run_async
def eightball(update: Update, context: CallbackContext):
    reply_text = (
        update.effective_message.reply_to_message.reply_text
        if update.effective_message.reply_to_message
        else update.effective_message.reply_text
    )
    reply_text(random.choice(fun_strings.EIGHTBALL))


@run_async
def table(update: Update, context: CallbackContext):
    reply_text = (
        update.effective_message.reply_to_message.reply_text
        if update.effective_message.reply_to_message
        else update.effective_message.reply_text
    )
    reply_text(random.choice(fun_strings.TABLE))


normiefont = [
    "a",
    "b",
    "c",
    "d",
    "e",
    "f",
    "g",
    "h",
    "i",
    "j",
    "k",
    "l",
    "m",
    "n",
    "o",
    "p",
    "q",
    "r",
    "s",
    "t",
    "u",
    "v",
    "w",
    "x",
    "y",
    "z",
]
weebyfont = [
    "卂",
    "乃",
    "匚",
    "刀",
    "乇",
    "下",
    "厶",
    "卄",
    "工",
    "丁",
    "长",
    "乚",
    "从",
    "𠘨",
    "口",
    "尸",
    "㔿",
    "尺",
    "丂",
    "丅",
    "凵",
    "リ",
    "山",
    "乂",
    "丫",
    "乙",
]


@run_async
def say(update: Update, context: CallbackContext):
    args = context.args
    message = update.effective_message
    string = ""

    if message.reply_to_message:
        string = message.reply_to_message.text.lower().replace(" ", "  ")

    if args:
        string = "  ".join(args).lower()

    if not string:
        message.reply_text("Usage is `/weebify <text>`", parse_mode=ParseMode.MARKDOWN)
        return

    for normiecharacter in string:
        if normiecharacter in normiefont:
            normiecharacter = normiefont[normiefont.index(normiecharacter)]
            string = string.replace(normiecharacter, normiecharacter)

    if message.reply_to_message:
        message.reply_to_message.reply_text(string)
    else:
        message.reply_text(string)


__help__ = """
 ❍ /kiss*:* Responde al mensaje de un usuario para besarlo
 ❍ /hug*:* Responde al mensaje de un usuario para abrazarlo
 ❍ /judge*:* Juzga si un usuario miente o dice la verdad
 ❍ /runs*:* Responde una cadena aleatoria de un array de respuestas
 ❍ /slap*:* Abofetear a un usuario, o recibir una bofetada si no es una respuesta
 ❍ /shrug*:* Encogerse de hombros XD
 ❍ /table*:* Obtener flip/unflip :v
 ❍ /decide*:* Responde aleatoriamente sí/no/tal vez
 ❍ /toss*:* Lanza una moneda
 ❍ /bluetext*:* Compruébelo usted mismo :V
 ❍ /roll*:* Tira un dado
 ❍ /rlg*:* Une orejas,nariz,boca y crea un emo ;-;
 ❍ /shout <palabra clave>*:* Escribe lo que quieras para dar un grito fuerte
 ❍ /weebify <texto>*:* Devuelve un texto weebificado
 ❍ /sanitize*:* Úsalo siempre antes de /pat o cualquier contacto
 ❍ /pat*:* Da una palmadita a un usuario, o recibe una palmadita
 ❍ /8ball*:* Predice usando el método 8ball 
 ❍ `/say <mensaje>`*:* El bot repite el mensaje dado
"""

KISS_HANDLER = DisableAbleCommandHandler("kiss", kiss)
HUG_HANDLER = DisableAbleCommandHandler("hug", hug)
JUDGE_HANDLER = DisableAbleCommandHandler("judge", judge)
SANITIZE_HANDLER = DisableAbleCommandHandler("sanitize", sanitize)
RUNS_HANDLER = DisableAbleCommandHandler("runs", runs)
SLAP_HANDLER = DisableAbleCommandHandler("slap", slap)
PAT_HANDLER = DisableAbleCommandHandler("pat", pat)
ROLL_HANDLER = DisableAbleCommandHandler("roll", roll)
TOSS_HANDLER = DisableAbleCommandHandler("toss", toss)
SHRUG_HANDLER = DisableAbleCommandHandler("shrug", shrug)
BLUETEXT_HANDLER = DisableAbleCommandHandler("bluetext", bluetext)
RLG_HANDLER = DisableAbleCommandHandler("rlg", rlg)
DECIDE_HANDLER = DisableAbleCommandHandler("decide", decide)
EIGHTBALL_HANDLER = DisableAbleCommandHandler("8ball", eightball)
TABLE_HANDLER = DisableAbleCommandHandler("table", table)
SHOUT_HANDLER = DisableAbleCommandHandler("shout", shout)
SAY_HANDLER = DisableAbleCommandHandler("say", say)

dispatcher.add_handler(KISS_HANDLER)
dispatcher.add_handler(HUG_HANDLER)
dispatcher.add_handler(JUDGE_HANDLER)
dispatcher.add_handler(SAY_HANDLER)
dispatcher.add_handler(SHOUT_HANDLER)
dispatcher.add_handler(SANITIZE_HANDLER)
dispatcher.add_handler(RUNS_HANDLER)
dispatcher.add_handler(SLAP_HANDLER)
dispatcher.add_handler(PAT_HANDLER)
dispatcher.add_handler(ROLL_HANDLER)
dispatcher.add_handler(TOSS_HANDLER)
dispatcher.add_handler(SHRUG_HANDLER)
dispatcher.add_handler(BLUETEXT_HANDLER)
dispatcher.add_handler(RLG_HANDLER)
dispatcher.add_handler(DECIDE_HANDLER)
dispatcher.add_handler(EIGHTBALL_HANDLER)
dispatcher.add_handler(TABLE_HANDLER)

__mod_name__ = "Fun"
__command_list__ = [
    "kiss",
    "hug",
    "judge",
    "runs",
    "slap",
    "roll",
    "toss",
    "shrug",
    "bluetext",
    "rlg",
    "decide",
    "table",
    "pat",
    "sanitize",
    "shout",
    "weebify",
    "8ball",
    "say",
]
__handlers__ = [
    KISS_HANDLER,
    HUG_HANDLER,
    JUDGE_HANDLER,
    RUNS_HANDLER,
    SLAP_HANDLER,
    PAT_HANDLER,
    ROLL_HANDLER,
    TOSS_HANDLER,
    SHRUG_HANDLER,
    BLUETEXT_HANDLER,
    RLG_HANDLER,
    DECIDE_HANDLER,
    TABLE_HANDLER,
    SANITIZE_HANDLER,
    SHOUT_HANDLER,
    SAY_HANDLER,
    EIGHTBALL_HANDLER,
]
