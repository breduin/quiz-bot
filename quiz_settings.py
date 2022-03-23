"""Установки викторины"""

class MenuItems:
    """Команды пользователя"""
    NEW_QUESTION = 'Новый вопрос'
    NEW_QUIZ = 'Новая викторина'
    GIVE_UP = 'Сдаться'
    SCORE = 'Мой счёт'
    FINISH = 'Закончить'
    QUIT = 'Выйти'


class BotMessages:
    """Ответы/сообщения бота"""
    CORRECT_ANSWER = 'Правильный ответ!'
    WRONG_ANSWER = 'Неправильный ответ! Попробуешь еще раз?'
    HELLO_MESSAGE = 'Привет'
    BYE_MESSAGE = 'Пока'
    HELP_MESSAGE = '''Для навигации используй кнопки.
    Если хочешь начать викторину, набери /start.
    Если хочешь закончить, набери /bye.'''
    NEW_QUIZ_MESSAGE = 'Начинаем новую викторину! Жми кнопку!'


# Папка с файлами вопросов викторины
QUESTIONS_DIR = 'qanda'

# Степень совпадения ответа пользователя с эталонным ответом
COINCIDENCE_RATE = 0.5


VK_API_URL = 'https://api.vk.com/method/users.get'
