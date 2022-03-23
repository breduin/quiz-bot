"""TG bot for Quiz"""

import logging
import redis

from environs import Env
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler
from telegram.ext import Filters, CallbackContext
from telegram.ext import ConversationHandler

from logs_handlers import TelegramBotHandler
from questions import QuestionFileIssue
from questions import get_quiz_filenames
from quiz_settings import MenuItems as mi
from quiz_settings import QUESTIONS_DIR
from states import ANSWERING, QUESTIONING
from tg_commands import start
from tg_commands import bye
from tg_commands import get_answer
from tg_commands import get_count
from tg_commands import get_quiz
from tg_commands import ask_question
from tg_commands import start_new_quiz
from tg_commands import finish_quiz
from tg_commands import give_up
from tg_commands import handle_vogue_message


logger = logging.getLogger(__name__)


def handle_tg_error(update: Update, context: CallbackContext) -> None:
    """Send message to logger bot"""
    logger.error(msg="TG-bot: Исключение при обработке сообщения:",
                 exc_info=context.error
                 )


def main() -> None:
    """Start the bot."""
    logger.setLevel(logging.INFO)
    env = Env()
    env.read_env()

    quizzes_queue = QuestionFileIssue(get_quiz_filenames(QUESTIONS_DIR))

    r = redis.Redis(
        host=env.str('REDIS_HOST'),
        port=env('REDIS_PORT'),
        password=env.str('REDIS_PASSWORD')
        )

    def initialize_quiz(update: Update, context: CallbackContext):
        context.chat_data.clear()
        context.chat_data.setdefault('count_questions', 0)
        context.chat_data.setdefault('correct_answers', 0)
        context.chat_data['quizzes_queue'] = quizzes_queue
        context.chat_data['questions_queue'] = get_quiz(update, context)
        context.chat_data['database'] = r
        return start(update, context)

    bot_handler = TelegramBotHandler(env.str('TG_LOGGER_TOKEN'),
                                     env.str('TG_LOGGING_CHAT_ID')
                                     )
    bot_formatter = logging.Formatter('%(message)s')
    bot_handler.setFormatter(bot_formatter)
    logger.addHandler(bot_handler)

    updater = Updater(env.str('TG_TOKEN'))
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', initialize_quiz),
            CommandHandler('bye', bye)
            ],

        states={
            QUESTIONING: [
                MessageHandler(Filters.text(mi.NEW_QUESTION) & ~Filters.command, ask_question),
                MessageHandler(Filters.text(mi.SCORE) & ~Filters.command, get_count),
                MessageHandler(Filters.text(mi.FINISH) & ~Filters.command, finish_quiz),
                MessageHandler(Filters.text & ~Filters.command, handle_vogue_message),
            ],
            ANSWERING: [
                MessageHandler(Filters.text(mi.NEW_QUESTION) & ~Filters.command, ask_question),
                MessageHandler(Filters.text(mi.GIVE_UP) & ~Filters.command, give_up),
                MessageHandler(Filters.text(mi.SCORE) & ~Filters.command, get_count),
                MessageHandler(Filters.text(mi.FINISH) & ~Filters.command, finish_quiz),
                MessageHandler(Filters.text(mi.QUIT) & ~Filters.command, bye),
                MessageHandler(Filters.text(mi.NEW_QUIZ) & ~Filters.command, start_new_quiz),
                MessageHandler(Filters.text & ~Filters.command, get_answer),
            ],
        },

        fallbacks=[MessageHandler(Filters.text & ~Filters.command, handle_vogue_message)]
    )

    dispatcher.add_handler(conv_handler)
    dispatcher.add_error_handler(handle_tg_error)

    logger.info('TG quiz bot started.')
    try:
        updater.start_polling()
        updater.idle()
    except KeyboardInterrupt:
        logger.info('TG quiz bot stoppped.')
        exit()


if __name__ == '__main__':
    main()
