import os
from os.path import join


class QuestionIssue:
    """Получить вопросы викторины по одному."""
    def __init__(self, questions):
        self._questions = questions

    def pick(self):
        try:
            return self._questions.pop()
        except IndexError:
            raise LookupError('Вопросы закончились!')

    def __call__(self):
        return self.pick()


class QuestionFileIssue:
    """Получить файлы с вопросами викторин по одному."""
    def __init__(self, filenames):
        self._filenames = filenames

    def pick(self):
        try:
            return self._filenames.pop()
        except IndexError:
            raise LookupError('Файлы с викторинами закончились!')

    def __call__(self):
        return self.pick()


def get_quiz_filenames(directory):
    return [join(directory, filename) for filename in os.listdir(directory)]


def get_qanda(quiz_filename: str) -> dict:
    """Получить словарь с вопросами и ответами из файла quiz_filename"""
    with open(quiz_filename, 'r', encoding='KOI8-R') as my_file:
        file_content = my_file.read()

    qanda = {}
    sections = file_content.split('Ответ:')
    for i in range(1, len(sections)):
        question_raw = sections[i-1].split('Вопрос')[-1]
        answer_raw = sections[i].split('Вопрос')[0]

        question_number = question_raw.split(':')[0].strip()
        if not question_number.isdigit():
            continue
        question = question_raw.split(':', maxsplit=1)[1].strip().replace('\n', ' ')

        answer_raw_splitted = answer_raw.split('\n')
        for item in answer_raw_splitted:
            if item:
                answer = item
                break

        complete_question = {
            'Вопрос': question,
            'Ответ': answer,
        }
        qanda_key = ' '.join(['Вопрос', question_number])
        qanda[qanda_key] = complete_question

    return qanda


if __name__ == '__main__':
    import pprint
    qanda = get_qanda('qanda/amo96.txt')
    pprint.pprint(qanda)
