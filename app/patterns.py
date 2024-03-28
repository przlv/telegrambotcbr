from telebot import types


def create_keyboard_menu() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=3)
    button1 = types.InlineKeyboardButton("Приезд", callback_data="get-arrival")
    button2 = types.InlineKeyboardButton("Отъезд", callback_data="get-departure")
    button3 = types.InlineKeyboardButton("Проживание", callback_data="get-hotel")
    markup.add(button1, button2, button3)
    return markup
