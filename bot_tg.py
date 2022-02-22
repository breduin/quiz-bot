"""TG bot for Verbs Game Publishing."""
import logging
import redis
import telegram

from environs import Env
from fuzzy_match import algorithims
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler
from telegram.ext import Filters, CallbackContext
from telegram.ext import ConversationHandler

from logs_handlers import TelegramBotHandler
from questions import get_qanda
from questions import QuestionIssue
from questions import QuestionFileIssue
from questions import get_quiz_filenames


logger = logging.getLogger(__name__)


QUESTIONING, ANSWERING = range(2)

# Запросы пользователя
NEW_QUESTION = 'Новый вопрос'
NEW_QUIZ = 'Новая викторина'
GIVE_UP = 'Сдаться'
SCORE = 'Мой счёт'
FINISH = 'Закончить'
QUIT = 'Выйти'


# Панели кнопок
COUNT_END_KEYBOARD = [SCORE, FINISH]
GIVEUP_KEYBOARD = [[GIVE_UP], COUNT_END_KEYBOARD]
NEW_QUESTION_KEYBOARD = [[NEW_QUESTION], COUNT_END_KEYBOARD]
NEW_QUIZ_KEYBOARD = [[NEW_QUIZ, QUIT]]
START_KEYBOARD = [[NEW_QUESTION], [FINISH]]


# Папка с файлами вопросов викторины
QUESTIONS_DIR = 'qanda'


def bye(update: Update, context: CallbackContext):
    """Send a message when the command /bye is issued."""
    context.chat_data.clear()
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'До свидания, {user.mention_markdown_v2()}\!',
        reply_markup=ForceReply(selective=True),
    )
    return ConversationHandler.END


def start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    user = update.effective_user
    custom_keyboard = START_KEYBOARD
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    update.message.reply_markdown_v2(
        fr'Здравствуйте\! {user.mention_markdown_v2()}\!',
        reply_markup=reply_markup,
    )
    return QUESTIONING


def finish_quiz(update: Update, context: CallbackContext):
    custom_keyboard = NEW_QUIZ_KEYBOARD
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    reply_message = f"""
        Вопросы закончились!
        Ваш счёт {context.chat_data['correct_answers']}
        из {context.chat_data['count_questions']}
        """

    update.message.reply_text(
        text=reply_message,
        reply_markup=reply_markup,
        )
    return ANSWERING


def handle_tg_error(update: Update, context: CallbackContext) -> None:
    """Send message to logger bot"""
    logger.error(msg="TG-bot: Исключение при обработке сообщения:",
                 exc_info=context.error
                 )


def ask_question(update: Update, context: CallbackContext):
    session_id = update.message.from_user.id
    questions_queue = context.chat_data.get('questions_queue')
    r = context.chat_data['database']
    try:
        question_block = questions_queue.pick()
    except LookupError:
        return finish_quiz(update, context)
    else:
        context.chat_data['count_questions'] += 1
        r.set(session_id, question_block['Ответ'].encode())
        custom_keyboard = GIVEUP_KEYBOARD
        reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
        reply_message = f"{question_block['N']}: {question_block['Вопрос']}"

    update.message.reply_text(
        text=reply_message,
        reply_markup=reply_markup,
        )
    return ANSWERING


def get_count(update: Update, context: CallbackContext):
    custom_keyboard = GIVEUP_KEYBOARD
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    reply_message = f"""
        Ваш счёт {context.chat_data['correct_answers']}
        из {context.chat_data['count_questions']}
        """
    update.message.reply_text(
        text=reply_message,
        reply_markup=reply_markup,
        )
    return ANSWERING


def give_up(update: Update, context: CallbackContext):
    r = context.chat_data['database']
    session_id = update.message.from_user.id
    answer = r.get(session_id).decode().split('.')[0]
    custom_keyboard = NEW_QUESTION_KEYBOARD
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    reply_message = f'Ответ: {answer}'

    update.message.reply_text(
        text=reply_message,
        reply_markup=reply_markup,
        )
    return QUESTIONING


def get_answer(update: Update, context: CallbackContext):
    session_id = update.message.from_user.id
    r = context.chat_data['database']

    if not (text := update.message.text):
        return handle_vogue_message(update, context)

    answer = r.get(session_id).decode().split('.')[0]
    coincidence_rate = algorithims.trigram(text, answer)
    if coincidence_rate >= 0.5:
        context.chat_data['correct_answers'] += 1
        r.delete(session_id)
        custom_keyboard = NEW_QUESTION_KEYBOARD
        reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
        reply_message = f'Правильный ответ! ({answer})'
    else:
        custom_keyboard = GIVEUP_KEYBOARD
        reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
        reply_message = 'Неправильный ответ! Попробуешь еще раз?'

    update.message.reply_text(
        text=reply_message,
        reply_markup=reply_markup,
        )
    return ANSWERING


def get_quiz(update: Update, context: CallbackContext):
    quizzes_queue = context.chat_data['quizzes_queue']
    quiz_filename = quizzes_queue.pick()

    qanda = get_qanda(quiz_filename)
    questions = [
        {
            'N': q,
            'Вопрос': qanda[q]['Вопрос'],
            'Ответ': qanda[q]['Ответ'],
        } for q in qanda.keys()
        ]
    questions.sort(key=lambda x: int(x['N'].split()[-1]), reverse=True)
    questions_queue = QuestionIssue(questions)

    return questions_queue


def start_new_quiz(update: Update, context: CallbackContext):
    context.chat_data['questions_queue'] = get_quiz(update, context)
    custom_keyboard = NEW_QUESTION_KEYBOARD
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    reply_message = 'Начинаем новую викторину!'

    update.message.reply_text(
        text=reply_message,
        reply_markup=reply_markup,
        )
    return QUESTIONING


def handle_vogue_message(update: Update, context: CallbackContext):
    custom_keyboard = [
        [NEW_QUESTION_KEYBOARD[0], GIVEUP_KEYBOARD[0]],
        [NEW_QUIZ_KEYBOARD[0]],
        COUNT_END_KEYBOARD
        ]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    reply_message = 'Не могу разобрать твое сообщение, уточни'

    update.message.reply_text(
        text=reply_message,
        reply_markup=reply_markup,
        )
    return ANSWERING


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
                MessageHandler(Filters.text(SCORE) & ~Filters.command, get_count),
                MessageHandler(Filters.text(FINISH) & ~Filters.command, finish_quiz),
                MessageHandler(Filters.text & ~Filters.command, ask_question),
            ],
            ANSWERING: [
                MessageHandler(Filters.text(NEW_QUESTION) & ~Filters.command, ask_question),
                MessageHandler(Filters.text(GIVE_UP) & ~Filters.command, give_up),
                MessageHandler(Filters.text(SCORE) & ~Filters.command, get_count),
                MessageHandler(Filters.text(FINISH) & ~Filters.command, finish_quiz),
                MessageHandler(Filters.text(QUIT) & ~Filters.command, bye),
                MessageHandler(Filters.text(NEW_QUIZ) & ~Filters.command, start_new_quiz),
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
