@echo off
TITLE Zhongli bot
:: Enables virtual env mode and then starts zhongli
env\scripts\activate.bat && py -m tg_bot
