import time
from cachetools import LRUCache
from telegram import Update
from tg_bot.modules.disable import DisableAbleCommandHandler, DisableAbleMessageHandler
from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, InlineQueryHandler, CallbackContext
from telegram.ext.filters import BaseFilter, Filters
from tg_bot import dispatcher as d, log
from typing import Optional, List

user_history_cache = LRUCache(maxsize=1000)  # Adjust maxsize as needed

def rate_limit(messages_per_window: int, window_seconds: int):
    """
    Decorator that limits the rate at which a function can be called.

    Args:
        messages_per_window (int): The maximum number of messages allowed within the specified window.
        window_seconds (int): The duration of the window in seconds.

    Returns:
        function: The decorated function.

    Example:
        @rate_limit(5, 60)  # Allow 5 messages per minute
        def process_message(update: Update, context: CallbackContext):
            # Process the message
    """
    def decorator(func):
        def wrapper(update: Update, context: CallbackContext):
            user_id = update.effective_user.id
            current_time = time.time()

            message_history = user_history_cache[user_id] if user_id in user_history_cache else []
            # print(message_history)
            message_history = [t for t in message_history if current_time - t <= window_seconds]

            if len(message_history) >= messages_per_window:
                log.info(f"Rate limit exceeded for user {user_id}. Allowed {messages_per_window} updates in {window_seconds} seconds.")
                return

            message_history.append(current_time)
            user_history_cache[user_id] = message_history
            func(update, context)

        return wrapper

    return decorator

class KigyoTelegramHandler:
    """
    A class that provides decorators for registering command, message, callback query, and inline query handlers
    with the Telegram Bot API.
    """

    def __init__(self, d):
        self._dispatcher = d

    def command(
            self, command: str, filters: Optional[BaseFilter] = None, admin_ok: bool = False, pass_args: bool = False,
            pass_chat_data: bool = False, run_async: bool = True, can_disable: bool = True,
            group: Optional[int] = 40
    ):
        """
        Decorator for registering a command handler with the Telegram Bot API.

        Args:
            command (str): The command string.
            filters (Optional[BaseFilter]): Filters to apply to the command handler.
            admin_ok (bool): Whether the command can be executed by admins only.
            pass_args (bool): Whether to pass command arguments to the handler.
            pass_chat_data (bool): Whether to pass chat data to the handler.
            run_async (bool): Whether the handler should be executed asynchronously.
            can_disable (bool): Whether the command can be disabled.
            group (Optional[int]): The group ID for ordering the command handlers.

        Returns:
            Callable: The decorated function.
        """
        if filters:
           filters = filters & ~Filters.update.edited_message
        else:
            filters = ~Filters.update.edited_message
        def _command(func):
            try:
                if can_disable:
                    self._dispatcher.add_handler(
                        DisableAbleCommandHandler(command, func, filters=filters, run_async=run_async,
                                                  pass_args=pass_args, admin_ok=admin_ok), group
                    )
                else:
                    self._dispatcher.add_handler(
                        CommandHandler(command, func, filters=filters, run_async=run_async, pass_args=pass_args), group
                    )
                log.debug(f"[KIGCMD] Loaded handler {command} for function {func.__name__} in group {group}")
            except TypeError:
                if can_disable:
                    self._dispatcher.add_handler(
                        DisableAbleCommandHandler(command, func, filters=filters, run_async=run_async,
                                                  pass_args=pass_args, admin_ok=admin_ok, pass_chat_data=pass_chat_data)
                    )
                else:
                    self._dispatcher.add_handler(
                        CommandHandler(command, func, filters=filters, run_async=run_async, pass_args=pass_args,
                                       pass_chat_data=pass_chat_data)
                    )
                log.debug(f"[KIGCMD] Loaded handler {command} for function {func.__name__}")

            return func

        return _command

    def message(self, pattern: Optional[BaseFilter] = None, can_disable: bool = True, run_async: bool = True,
                group: Optional[int] = 60, friendly=None):
        """
        Decorator for registering a message handler with the Telegram Bot API.

        Args:
            pattern (Optional[BaseFilter]): Filters to apply to the message handler.
            can_disable (bool): Whether the message handler can be disabled.
            run_async (bool): Whether the handler should be executed asynchronously.
            group (Optional[int]): The group ID for ordering the message handlers.
            friendly: A friendly name for the handler.

        Returns:
            Callable: The decorated function.
        """
        if pattern:
           pattern = pattern & ~Filters.update.edited_message
        else:
           pattern = ~Filters.update.edited_message
        def _message(func):
            try:
                if can_disable:
                    self._dispatcher.add_handler(
                        DisableAbleMessageHandler(pattern, func, friendly=friendly, run_async=run_async), group
                    )
                else:
                    self._dispatcher.add_handler(
                        MessageHandler(pattern, func, run_async=run_async), group
                    )
                log.debug(f"[KIGMSG] Loaded filter pattern {pattern} for function {func.__name__} in group {group}")
            except TypeError:
                if can_disable:
                    self._dispatcher.add_handler(
                        DisableAbleMessageHandler(pattern, func, friendly=friendly, run_async=run_async)
                    )
                else:
                    self._dispatcher.add_handler(
                        MessageHandler(pattern, func, run_async=run_async)
                    )
                log.debug(f"[KIGMSG] Loaded filter pattern {pattern} for function {func.__name__}")

            return func

        return _message

    def callbackquery(self, pattern: str = None, run_async: bool = True):
        """
        Decorator for registering a callback query handler with the Telegram Bot API.

        Args:
            pattern (str): The pattern string.
            run_async (bool): Whether the handler should be executed asynchronously.

        Returns:
            Callable: The decorated function.
        """
        def _callbackquery(func):
            self._dispatcher.add_handler(CallbackQueryHandler(pattern=pattern, callback=func, run_async=run_async))
            log.debug(f'[KIGCALLBACK] Loaded callbackquery handler with pattern {pattern} for function {func.__name__}')
            return func

        return _callbackquery

    def inlinequery(self, pattern: Optional[str] = None, run_async: bool = True, pass_user_data: bool = True,
                    pass_chat_data: bool = True, chat_types: List[str] = None):
        """
        Decorator for registering an inline query handler with the Telegram Bot API.

        Args:
            pattern (Optional[str]): The pattern string.
            run_async (bool): Whether the handler should be executed asynchronously.
            pass_user_data (bool): Whether to pass user data to the handler.
            pass_chat_data (bool): Whether to pass chat data to the handler.
            chat_types (List[str]): The types of chats to handle.

        Returns:
            Callable: The decorated function.
        """
        def _inlinequery(func):
            self._dispatcher.add_handler(
                InlineQueryHandler(pattern=pattern, callback=func, run_async=run_async, pass_user_data=pass_user_data,
                                   pass_chat_data=pass_chat_data, chat_types=chat_types))
            log.debug(
                f'[KIGINLINE] Loaded inlinequery handler with pattern {pattern} for function {func.__name__} | PASSES '
                f'USER DATA: {pass_user_data} | PASSES CHAT DATA: {pass_chat_data} | CHAT TYPES: {chat_types}')
            return func

        return _inlinequery


kigcmd = KigyoTelegramHandler(d).command
kigmsg = KigyoTelegramHandler(d).message
kigcallback = KigyoTelegramHandler(d).callbackquery
kiginline = KigyoTelegramHandler(d).inlinequery
