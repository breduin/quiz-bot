"""TG bot handler for logging."""
import logging
import telegram


class TelegramBotHandler(logging.Handler):

    def __init__(self, token, chat_id, level=logging.NOTSET):
        self.chat_id = chat_id
        self.bot = telegram.Bot(token=token)
        super().__init__(level=level)

    def emit(self, record):
        log_entry = self.format(record)
        self.bot.send_message(
            chat_id=self.chat_id,
            text=log_entry
            )
