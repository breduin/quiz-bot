from fuzzy_match import algorithims
from vk_api.utils import get_random_id

from emulators import CallbackContext
from emulators import Update
from questions import get_qanda
from questions import QuestionIssue
from quiz_settings import COINCIDENCE_RATE
from vk_keyboards import GIVEUP_KEYBOARD
from vk_keyboards import NEW_QUESTION_KEYBOARD
from vk_keyboards import NEW_QUIZ_KEYBOARD


def start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    vk_api = context.chat_data['vk_api']
    event = context.chat_data['event']
    user = context.chat_data['user']
    reply_message = f'Привет, {user}! Начинаем викторину!'
    vk_api.messages.send(
        user_id=event.user_id,
        random_id=get_random_id(),
        message=reply_message
        )
    context.chat_data['is_answering'] = True
    return ask_question(update, context)


def bye(update: Update, context: CallbackContext):
    """Send a message when the command /bye is issued or QUIT is choosen."""
    vk_api = context.chat_data['vk_api']
    event = context.chat_data['event']
    user = context.chat_data['user']
    custom_keyboard = GIVEUP_KEYBOARD
    reply_message = f'Пока, {user}!'
    context.chat_data['is_answering'] = False
    context.chat_data.setdefault('count_questions', 0)
    context.chat_data.setdefault('correct_answers', 0)
    vk_api.messages.send(
        user_id=event.user_id,
        random_id=get_random_id(),
        keyboard=custom_keyboard.get_empty_keyboard(),
        message=reply_message
        )


def get_count(update: Update, context: CallbackContext):
    vk_api = context.chat_data['vk_api']
    event = context.chat_data['event']
    custom_keyboard = NEW_QUESTION_KEYBOARD
    reply_message = f"""
        Ваш счёт {context.chat_data['correct_answers']} из {context.chat_data['count_questions']}
        """
    vk_api.messages.send(
        user_id=event.user_id,
        random_id=get_random_id(),
        keyboard=custom_keyboard.get_keyboard(),
        message=reply_message
        )


def finish_quiz(update: Update, context: CallbackContext):
    vk_api = context.chat_data['vk_api']
    event = context.chat_data['event']
    custom_keyboard = NEW_QUIZ_KEYBOARD
    reply_message = f"""
        Вопросы закончились!
        Ваш счёт {context.chat_data['correct_answers']} из {context.chat_data['count_questions']}
        """

    vk_api.messages.send(
        user_id=event.user_id,
        random_id=get_random_id(),
        keyboard=custom_keyboard.get_keyboard(),
        message=reply_message
        )


def ask_question(update: Update, context: CallbackContext):
    vk_api = context.chat_data['vk_api']
    event = context.chat_data['event']
    session_id = event.user_id
    questions_queue = context.chat_data.get('questions_queue')
    database = context.chat_data['database']
    context.chat_data['is_answering'] = True
    try:
        question_block = questions_queue.pick()
    except LookupError:
        return finish_quiz(update, context)
    else:
        context.chat_data['count_questions'] += 1
        database.set(session_id, question_block['Ответ'].encode())
        custom_keyboard = GIVEUP_KEYBOARD
        reply_message = f"{question_block['N']}: {question_block['Вопрос']}"

    vk_api.messages.send(
        user_id=event.user_id,
        random_id=get_random_id(),
        keyboard=custom_keyboard.get_keyboard(),
        message=reply_message
        )


def give_up(update: Update, context: CallbackContext):
    vk_api = context.chat_data['vk_api']
    event = context.chat_data['event']
    r = context.chat_data['database']
    session_id = event.user_id
    answer = r.get(session_id).decode().split('.')[0]
    custom_keyboard = NEW_QUESTION_KEYBOARD
    reply_message = f'Ответ: {answer}'

    vk_api.messages.send(
        user_id=event.user_id,
        random_id=get_random_id(),
        keyboard=custom_keyboard.get_keyboard(),
        message=reply_message
        )


def get_answer(update: Update, context: CallbackContext):
    vk_api = context.chat_data['vk_api']
    event = context.chat_data['event']
    session_id = event.user_id
    database = context.chat_data['database']

    answer = database.get(session_id).decode().split('.')[0]
    coincidence_rate = algorithims.trigram(event.text, answer)
    if coincidence_rate >= COINCIDENCE_RATE:
        context.chat_data['correct_answers'] += 1
        database.delete(session_id)
        custom_keyboard = NEW_QUESTION_KEYBOARD
        reply_message = f'Правильный ответ! ({answer})'
        context.chat_data['is_answering'] = False
    else:
        custom_keyboard = GIVEUP_KEYBOARD
        reply_message = 'Неправильный ответ! Попробуешь еще раз?'

    vk_api.messages.send(
        user_id=event.user_id,
        random_id=get_random_id(),
        keyboard=custom_keyboard.get_keyboard(),
        message=reply_message
        )


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
    vk_api = context.chat_data['vk_api']
    event = context.chat_data['event']
    context.chat_data['questions_queue'] = get_quiz(update, context)
    reply_message = 'Начинаем новую викторину!'

    vk_api.messages.send(
        user_id=event.user_id,
        random_id=get_random_id(),
        message=reply_message
        )
    return start(update, context)


def handle_vogue_message(update: Update, context: CallbackContext):
    vk_api = context.chat_data['vk_api']
    event = context.chat_data['event']
    reply_message = '''Не могу разобрать команду, уточни.
    Для навигации используй кнопки.
    Если хочешь начать викторину, набери /start.
    Если хочешь закончить, набери /bye.
    '''

    vk_api.messages.send(
        user_id=event.user_id,
        random_id=get_random_id(),
        message=reply_message
        )
