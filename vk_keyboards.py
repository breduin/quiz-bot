from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from quiz_settings import MenuItems


# Панели кнопок
GIVEUP_KEYBOARD = VkKeyboard(one_time=False)
GIVEUP_KEYBOARD.add_button(MenuItems.GIVE_UP, color=VkKeyboardColor.SECONDARY)
GIVEUP_KEYBOARD.add_line()
GIVEUP_KEYBOARD.add_button(MenuItems.FINISH, color=VkKeyboardColor.NEGATIVE)

NEW_QUESTION_KEYBOARD = VkKeyboard(one_time=False)
NEW_QUESTION_KEYBOARD.add_button(MenuItems.NEW_QUESTION, color=VkKeyboardColor.POSITIVE)
NEW_QUESTION_KEYBOARD.add_line()
NEW_QUESTION_KEYBOARD.add_button(MenuItems.SCORE, color=VkKeyboardColor.PRIMARY)
NEW_QUESTION_KEYBOARD.add_button(MenuItems.FINISH, color=VkKeyboardColor.NEGATIVE)

NEW_QUIZ_KEYBOARD = VkKeyboard(one_time=False)
NEW_QUIZ_KEYBOARD.add_button(MenuItems.NEW_QUIZ, color=VkKeyboardColor.POSITIVE)
NEW_QUIZ_KEYBOARD.add_button(MenuItems.QUIT, color=VkKeyboardColor.NEGATIVE)
