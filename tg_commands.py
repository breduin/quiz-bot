import telegram

from fuzzy_match import algorithims
from telegram import ForceReply
from telegram import Update
from telegram.ext import ConversationHandler
from telegram.ext import CallbackContext

from states import ANSWERING, QUESTIONING
from questions import get_qanda
from questions import QuestionIssue
from quiz_settings import COINCIDENCE_RATE
from quiz_settings import BotMessages as bm
from tg_keyboards import GIVEUP_KEYBOARD
from tg_keyboards import NEW_QUESTION_KEYBOARD
from tg_keyboards import NEW_QUIZ_KEYBOARD
from tg_keyboards import START_KEYBOARD


def _get_count(update: Update, context: CallbackContext):
    correct_answers = context.chat_data['correct_answers']
    count_questions = context.chat_data['count_questions']
    return f'Ваш счёт {correct_answers} из {count_questions}'


def bye(update: Update, context: CallbackContext):
    """Send a message when the command /bye is issued."""
    context.chat_data.clear()
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'{bm.BYE_MESSAGE}, {user.mention_markdown_v2()}\! Набери \/start, если захочешь поиграть ещё\.',
        reply_markup=ForceReply(selective=True),
    )
    return ConversationHandler.END


def start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    user = update.effective_user
    custom_keyboard = START_KEYBOARD
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    update.message.reply_markdown_v2(
        fr'{bm.HELLO_MESSAGE}, {user.mention_markdown_v2()}\!',
        reply_markup=reply_markup,
    )
    return QUESTIONING


def finish_quiz(update: Update, context: CallbackContext):
    custom_keyboard = NEW_QUIZ_KEYBOARD
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    reply_message = f'Вопросы закончились! {_get_count(update, context)}'

    update.message.reply_text(
        text=reply_message,
        reply_markup=reply_markup,
        )
    return ANSWERING


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
    custom_keyboard = NEW_QUESTION_KEYBOARD
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    reply_message = _get_count(update, context)
    update.message.reply_text(
        text=reply_message,
        reply_markup=reply_markup,
        )
    return ANSWERING


def give_up(update: Update, context: CallbackContext):
    database = context.chat_data['database']
    session_id = update.message.from_user.id
    answer = database.get(session_id).decode().split('.')[0]
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
    database = context.chat_data['database']

    if not (text := update.message.text):
        return handle_vogue_message(update, context)

    answer = database.get(session_id).decode().split('.')[0]
    coincidence_rate = algorithims.trigram(text, answer)
    if coincidence_rate >= COINCIDENCE_RATE:
        context.chat_data['correct_answers'] += 1
        database.delete(session_id)
        custom_keyboard = NEW_QUESTION_KEYBOARD
        reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
        reply_message = f'{bm.CORRECT_ANSWER} ({answer})'
        update.message.reply_text(
            text=reply_message,
            reply_markup=reply_markup,
            )
        return QUESTIONING

    custom_keyboard = GIVEUP_KEYBOARD
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    reply_message = bm.WRONG_ANSWER
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
    reply_message = bm.NEW_QUIZ_MESSAGE

    update.message.reply_text(
        text=reply_message,
        reply_markup=reply_markup,
        )
    return ANSWERING


def handle_vogue_message(update: Update, context: CallbackContext):
    reply_message = f'Не могу разобрать команду, уточни. {bm.HELP_MESSAGE}'

    update.message.reply_text(
        text=reply_message,
        )
    return ANSWERING
