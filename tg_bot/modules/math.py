from typing import List
import requests
from telegram import Message, Update, Bot, MessageEntity
from telegram.ext import CommandHandler
from tg_bot import dispatcher
from tg_bot.modules.disable import DisableAbleCommandHandler
import pynewtonmath as newton
import math



def simplify(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message
    message.reply_text(newton.simplify("{}".format(args[0])))



def factor(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message
    message.reply_text(newton.factor("{}".format(args[0])))



def derive(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message
    message.reply_text(newton.derive("{}".format(args[0])))



def integrate(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message
    message.reply_text(newton.integrate("{}".format(args[0])))



def zeroes(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message
    message.reply_text(newton.zeroes("{}".format(args[0])))



def tangent(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message
    message.reply_text(newton.tangent("{}".format(args[0])))



def area(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message
    message.reply_text(newton.area("{}".format(args[0])))



def cos(bot: Bot, update: Update, args):
    message = update.effective_message
    message.reply_text(math.cos(int(args[0])))



def sin(bot: Bot, update: Update, args):
    message = update.effective_message
    message.reply_text(math.sin(int(args[0])))



def tan(bot: Bot, update: Update, args):
    message = update.effective_message
    message.reply_text(math.tan(int(args[0])))



def arccos(bot: Bot, update: Update, args):
    message = update.effective_message
    message.reply_text(math.acos(int(args[0])))



def arcsin(bot: Bot, update: Update, args):
    message = update.effective_message
    message.reply_text(math.asin(int(args[0])))



def arctan(bot: Bot, update: Update, args):
    message = update.effective_message
    message.reply_text(math.atan(int(args[0])))



def abs(bot: Bot, update: Update, args):
    message = update.effective_message
    message.reply_text(math.fabs(int(args[0])))



def log(bot: Bot, update: Update, args):
    message = update.effective_message
    message.reply_text(math.log(int(args[0])))


SIMPLIFY_HANDLER = DisableAbleCommandHandler("math", simplify, pass_args=True, run_async=True)
FACTOR_HANDLER = DisableAbleCommandHandler("factor", factor, pass_args=True, run_async=True)
DERIVE_HANDLER = DisableAbleCommandHandler("derive", derive, pass_args=True, run_async=True)
INTEGRATE_HANDLER = DisableAbleCommandHandler("integrate", integrate, pass_args=True, run_async=True)
ZEROES_HANDLER = DisableAbleCommandHandler("zeroes", zeroes, pass_args=True, run_async=True)
TANGENT_HANDLER = DisableAbleCommandHandler("tangent", tangent, pass_args=True, run_async=True)
AREA_HANDLER = DisableAbleCommandHandler("area", area, pass_args=True, run_async=True)
COS_HANDLER = DisableAbleCommandHandler("cos", cos, pass_args=True, run_async=True)
SIN_HANDLER = DisableAbleCommandHandler("sin", sin, pass_args=True, run_async=True)
TAN_HANDLER = DisableAbleCommandHandler("tan", tan, pass_args=True, run_async=True)
ARCCOS_HANDLER = DisableAbleCommandHandler("arccos", arccos, pass_args=True, run_async=True)
ARCSIN_HANDLER = DisableAbleCommandHandler("arcsin", arcsin, pass_args=True, run_async=True)
ARCTAN_HANDLER = DisableAbleCommandHandler("arctan", arctan, pass_args=True, run_async=True)
ABS_HANDLER = DisableAbleCommandHandler("abs", abs, pass_args=True, run_async=True)
LOG_HANDLER = DisableAbleCommandHandler("log", log, pass_args=True, run_async=True)

dispatcher.add_handler(SIMPLIFY_HANDLER)
dispatcher.add_handler(FACTOR_HANDLER)
dispatcher.add_handler(DERIVE_HANDLER)
dispatcher.add_handler(INTEGRATE_HANDLER)
dispatcher.add_handler(ZEROES_HANDLER)
dispatcher.add_handler(TANGENT_HANDLER)
dispatcher.add_handler(AREA_HANDLER)
dispatcher.add_handler(COS_HANDLER)
dispatcher.add_handler(SIN_HANDLER)
dispatcher.add_handler(TAN_HANDLER)
dispatcher.add_handler(ARCCOS_HANDLER)
dispatcher.add_handler(ARCSIN_HANDLER)
dispatcher.add_handler(ARCTAN_HANDLER)
dispatcher.add_handler(ABS_HANDLER)
dispatcher.add_handler(LOG_HANDLER)
