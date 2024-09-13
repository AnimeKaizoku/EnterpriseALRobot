import logging
import time
import redis
from functools import wraps
from telegram import Update
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    InlineQueryHandler,
    CallbackContext,
    Filters,
)
from tg_bot import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD, dispatcher
from typing import Optional, List, Callable, Union
from tg_bot.modules.disable import DisableAbleCommandHandler, DisableAbleMessageHandler

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
)


def rate_limit(messages_per_window: int, window_seconds: int):
    def decorator(func):
        @wraps(func)
        def wrapper(update: Update, context: CallbackContext):
            user_id = update.effective_user.id
            current_time = time.time()
            key = f"rate_limit:{user_id}"

            user_history = redis_client.lrange(key, 0, -1)
            user_history = [
                float(t)
                for t in user_history
                if current_time - float(t) <= window_seconds
            ]

            if len(user_history) >= messages_per_window:
                logging.info(
                    f"Rate limit exceeded for user {user_id}. Allowed {messages_per_window} updates in {window_seconds} seconds."
                )
                return

            redis_client.lpush(key, current_time)
            redis_client.ltrim(key, 0, messages_per_window - 1)
            redis_client.expire(key, window_seconds)

            return func(update, context)

        return wrapper

    return decorator


class KigyoTelegramHandler:
    def __init__(self, dispatcher):
        self._dispatcher = dispatcher

    def _add_handler(self, handler, group: Optional[int] = None):
        if group is not None:
            self._dispatcher.add_handler(handler, group=group)
        else:
            self._dispatcher.add_handler(handler)

    def command(
        self,
        command: Union[str, List[str]],
        filters: Optional[Filters] = None,
        admin_ok: bool = False,
        pass_args: bool = False,
        pass_chat_data: bool = False,
        run_async: bool = True,
        can_disable: bool = True,
        group: Optional[int] = 40,
    ):
        def decorator(func: Callable):
            if isinstance(command, str):
                commands = [command]
            else:
                commands = command

            command_filter = Filters.command(commands)
            if filters:
                command_filter = command_filter & filters

            command_filter = command_filter & ~Filters.update.edited_message

            if can_disable:
                handler = DisableAbleCommandHandler(
                    commands,
                    func,
                    filters=command_filter,
                    run_async=run_async,
                    pass_args=pass_args,
                    admin_ok=admin_ok,
                    pass_chat_data=pass_chat_data,
                )
            else:
                handler = CommandHandler(
                    commands,
                    func,
                    filters=command_filter,
                    run_async=run_async,
                    pass_args=pass_args,
                    pass_chat_data=pass_chat_data,
                )

            self._add_handler(handler, group)
            logging.debug(
                f"[KIGCMD] Loaded handler {command} for function {func.__name__}"
            )
            return func

        return decorator

    def message(
        self,
        pattern: Optional[Filters] = None,
        can_disable: bool = True,
        run_async: bool = True,
        group: Optional[int] = 60,
        friendly: Optional[str] = None,
    ):
        def decorator(func: Callable):
            message_filter = pattern if pattern else Filters.all
            message_filter = message_filter & ~Filters.update.edited_message

            if can_disable:
                handler = DisableAbleMessageHandler(
                    message_filter, func, friendly=friendly, run_async=run_async
                )
            else:
                handler = MessageHandler(message_filter, func, run_async=run_async)

            self._add_handler(handler, group)
            logging.debug(f"[KIGMSG] Loaded filter for function {func.__name__}")
            return func

        return decorator

    def callbackquery(self, pattern: str = None, run_async: bool = True):
        def decorator(func: Callable):
            handler = CallbackQueryHandler(func, pattern=pattern, run_async=run_async)
            self._add_handler(handler)
            logging.debug(
                f"[KIGCALLBACK] Loaded callbackquery handler for function {func.__name__}"
            )
            return func

        return decorator

    def inlinequery(
        self,
        pattern: Optional[str] = None,
        run_async: bool = True,
        pass_user_data: bool = True,
        pass_chat_data: bool = True,
        chat_types: List[str] = None,
    ):
        def decorator(func: Callable):
            handler = InlineQueryHandler(
                func,
                pattern=pattern,
                run_async=run_async,
                pass_user_data=pass_user_data,
                pass_chat_data=pass_chat_data,
                chat_types=chat_types,
            )
            self._add_handler(handler)
            logging.debug(
                f"[KIGINLINE] Loaded inlinequery handler for function {func.__name__}"
            )
            return func

        return decorator


kigyo_handler = KigyoTelegramHandler(dispatcher)

kigcmd = kigyo_handler.command
kigmsg = kigyo_handler.message
kigcallback = kigyo_handler.callbackquery
kiginline = kigyo_handler.inlinequery
