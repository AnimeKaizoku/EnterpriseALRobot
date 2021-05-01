from tg_bot.modules.disable import DisableAbleCommandHandler
from telegram.ext import CommandHandler
from telegram.ext.filters import BaseFilter
from tg_bot import dispatcher as d, log
from typing import Optional, Union



class KigyoTelegramHandler:
    def __init__(self, d):
        self._dispatcher = d

    def command(
        self, command: str, filters: Optional[BaseFilter] = None, run_async: bool = True, can_disable: bool = True, group: Optional[Union[int]] = None
    ):


        def _command(func):
            try:
                if can_disable:
                    self._dispatcher.add_handler(
                        DisableAbleCommandHandler(command, func, filters=filters, run_async=run_async), group
                    )
                else:
                    self._dispatcher.add_handler(
                        CommandHandler(command, func, filters=filters, run_async=run_async), group
                    )
            except TypeError:
                if can_disable:
                    self._dispatcher.add_handler(
                        DisableAbleCommandHandler(command, func, filters=filters, run_async=run_async)
                    )
                else:
                    self._dispatcher.add_handler(
                        CommandHandler(command, func, filters=filters, run_async=run_async)
                    )
            log.info(f"[KIGCMD] Loaded handler {command} for function {func.__name__}")
            return func

        return _command

kigcmd = KigyoTelegramHandler(d).command
