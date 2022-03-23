from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from quiz_settings import MenuItems as mi


# Панели кнопок
GIVEUP_KEYBOARD = VkKeyboard(one_time=False)
GIVEUP_KEYBOARD.add_button(mi.GIVE_UP, color=VkKeyboardColor.SECONDARY)
GIVEUP_KEYBOARD.add_line()
GIVEUP_KEYBOARD.add_button(mi.FINISH, color=VkKeyboardColor.NEGATIVE)

NEW_QUESTION_KEYBOARD = VkKeyboard(one_time=False)
NEW_QUESTION_KEYBOARD.add_button(mi.NEW_QUESTION, color=VkKeyboardColor.POSITIVE)
NEW_QUESTION_KEYBOARD.add_line()
NEW_QUESTION_KEYBOARD.add_button(mi.SCORE, color=VkKeyboardColor.PRIMARY)
NEW_QUESTION_KEYBOARD.add_button(mi.FINISH, color=VkKeyboardColor.NEGATIVE)

NEW_QUIZ_KEYBOARD = VkKeyboard(one_time=False)
NEW_QUIZ_KEYBOARD.add_button(mi.NEW_QUIZ, color=VkKeyboardColor.POSITIVE)
NEW_QUIZ_KEYBOARD.add_button(mi.QUIT, color=VkKeyboardColor.NEGATIVE)
