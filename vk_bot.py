"""VK bot for Quiz"""

import logging
import redis
import requests
import vk_api as vk

from environs import Env
from logs_handlers import TelegramBotHandler
from vk_api.longpoll import VkLongPoll, VkEventType

from emulators import CallbackContext
from emulators import Update
from questions import QuestionFileIssue
from questions import get_quiz_filenames
from quiz_settings import MenuItems
from quiz_settings import QUESTIONS_DIR
from quiz_settings import VK_API_URL
from vk_commands import start
from vk_commands import bye
from vk_commands import get_answer
from vk_commands import get_count
from vk_commands import get_quiz
from vk_commands import ask_question
from vk_commands import start_new_quiz
from vk_commands import finish_quiz
from vk_commands import give_up
from vk_commands import handle_vogue_message


logger = logging.getLogger(__name__)


def main() -> None:
    """Start the bot."""
    logger.setLevel(logging.INFO)
    env = Env()
    env.read_env()

    # Logger-telegram-bot
    bot_handler = TelegramBotHandler(env.str('TG_LOGGER_TOKEN'),
                                     env.str('TG_LOGGING_CHAT_ID')
                                     )
    bot_formatter = logging.Formatter('%(message)s')
    bot_handler.setFormatter(bot_formatter)
    logger.addHandler(bot_handler)

    # Initialize VK session
    vk_session = vk.VkApi(token=env.str('VK_TOKEN'))
    vk_api = vk_session.get_api()

    # Initialize the quiz
    context = CallbackContext()
    update = Update()
    database = redis.Redis(
        host=env.str('REDIS_HOST'),
        port=env('REDIS_PORT'),
        password=env.str('REDIS_PASSWORD')
        )

    quizzes_queue = QuestionFileIssue(get_quiz_filenames(QUESTIONS_DIR))
    context.chat_data.setdefault('count_questions', 0)
    context.chat_data.setdefault('correct_answers', 0)
    context.chat_data['quizzes_queue'] = quizzes_queue
    context.chat_data['questions_queue'] = get_quiz(update, context)
    context.chat_data['database'] = database
    context.chat_data['vk_api'] = vk_api
    context.chat_data['is_answering'] = False

    # Start the bot
    logger.info('VK quiz bot started.')
    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            user = requests.get(
                VK_API_URL,
                params={
                    'user_ids': event.user_id,
                    'fields': 'sex',
                    'access_token': env.str('VK_TOKEN'),
                    'v': 5.81,
                    }
                ).json()['response'][0]['first_name']
            context.chat_data['event'] = event
            context.chat_data['user'] = user

            match event.text:
                case '/start':
                    start(update, context)
                case MenuItems.SCORE:
                    get_count(update, context)
                case MenuItems.FINISH:
                    finish_quiz(update, context)
                case MenuItems.NEW_QUESTION:
                    ask_question(update, context)
                case MenuItems.GIVE_UP:
                    give_up(update, context)
                case MenuItems.NEW_QUIZ:
                    start_new_quiz(update, context)
                case MenuItems.QUIT | '/bye':
                    bye(update, context)
                case _:
                    if context.chat_data['is_answering']:
                        get_answer(update, context)
                    else:
                        handle_vogue_message(update, context)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info('VK quiz bot stoppped.')
        exit()
