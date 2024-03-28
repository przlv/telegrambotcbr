import telebot
from telebot import types
import pandas as pd
from config import TOKEN, SECRET_CODE


# Функция для загрузки авторизованных пользователей
def load_authorized_users(df: pd.DataFrame):
    authorized_users = []
    for user in df.itertuples():
        if user.telegram_id != -1:
            authorized_users.append(user.telegram_id)
    return authorized_users

def update_df(df: pd.DataFrame):
    try:
        df.to_excel('./data.xlsx', index=False)
    except Exception as e:
        print(e)

def add_new_user(user_id, username):
    try:
        index = df.index[df['name_user'].str.lower() == username]
        df.loc[index, 'telegram_id'] = user_id
        update_df(df)
        return True
    except:
        return False

df = pd.read_excel('./data.xlsx')
authorized_users = load_authorized_users(df)

bot = telebot.TeleBot(TOKEN)
print('...:::Bot started:::...')


@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if is_user_authorized(user_id):
        bot.send_message(user_id, "Добро пожаловать в меню бота! /menu")
    else:
        bot.send_message(user_id, "Вы не авторизованы. Пожалуйста, авторизуйтесь /authorize.")


@bot.message_handler(commands=['authorize'])
def handle_register(message):
    if is_user_authorized(message.from_user.id):
        bot.send_message(message.chat.id, 'Вы уже авторизированы')
    else:
        msg = bot.send_message(message.chat.id,"Введите секретный код для регистрации")
        bot.register_next_step_handler(msg, check_secret_code)

def check_secret_code(message):
    if message.text == SECRET_CODE:
        msg = bot.send_message(message.chat.id, "Секретный код верен. Введите ваше в формате Имя Фамилия (Пример: Иван Иванов).")
        bot.register_next_step_handler(msg, process_register_step)
    else:
        bot.send_message(message.chat.id, "Неверный секретный код.")

def process_register_step(message):
    try:
        user_id = message.from_user.id
        username= message.text
        responce = register_user(user_id, username)
        if responce == 'user_added':
            bot.reply_to(message, "Вы успешно зарегистрированы!")
        elif responce == 'user_already_authorized':
            bot.reply_to(message, "Вы уже зарегистрированы.")
        else:
            bot.reply_to(message, f"Такого сотрудника нет: {message.text}\nПопробуйте ещераз")
            msg = bot.send_message(message.chat.id, "Введите ваше в формате Имя Фамилия (Пример: Иван Иванов).")
            bot.register_next_step_handler(msg, process_register_step)
    except Exception as e:
        bot.reply_to(message, 'Ошибка при регистрации.')
        print(e)

def register_user(user_id, username):
    # users_names = df['name_user'].tolist()
    username = username.strip().lower()
    user = df[df['name_user'].str.lower() == username].squeeze().T
    if not user.empty:
        if user.telegram_id == -1:
            add_new_user(user_id, username)
            authorized_users.append(user_id)
            return 'user_added'
        else:
            return 'user_already_authorized'
    else:
        return 'user_not_found'


def create_keyboard_menu():
    markup = types.InlineKeyboardMarkup(row_width=3)
    button1 = types.InlineKeyboardButton("Приезд", callback_data="get-arrival")
    button2 = types.InlineKeyboardButton("Отъезд", callback_data="get-departure")
    button3 = types.InlineKeyboardButton("Проживание", callback_data="get-hotel")
    markup.add(button1, button2, button3)
    return markup


@bot.message_handler(commands=['menu'])
def handle_menu(message):
    user_id = message.from_user.id
    if is_user_authorized(user_id):
        markup = create_keyboard_menu()
        bot.send_message(message.chat.id, "Выберите опцию:", reply_markup=markup)
    else:
        bot.send_message(user_id,
                         "Вы не авторизованы. Пожалуйста, авторизуйтесь сначала. /authorize")

@bot.callback_query_handler(func=lambda call: call.data.startswith('get'))
def query_handler_get(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    if call.data == "get-arrival":
        response = get_arrival_user(user_id)
    elif call.data == "get-departure":
        response = get_departure_user(user_id)
    elif call.data == "get-hotel":
        response = get_hotel_user(user_id)
    
    bot.answer_callback_query(callback_query_id=call.id)
    if response == call.message.text:
        return
    
    markup = create_keyboard_menu()
    try:
        # Пытаемся обновить существующее сообщение
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=response, reply_markup=markup)
    except telebot.apihelper.ApiTelegramException:
        # Если не получилось, отправляем новое сообщение
        bot.send_message(chat_id, response, reply_markup=markup)

def is_user_authorized(user_id):
    return user_id in authorized_users

def get_arrival_user(user_id):
    
    user = df[df['telegram_id'] == user_id].squeeze().T
    if not type(user.arrival) is str:
        pattern = 'Нету данных по прибытию'
    else:
        city, airport, arrival_time, flight_number = user.arrival.split(',')
        pattern = f"{user.name_user}, Вы прибываете в город {city}, {airport} в {arrival_time}.\nВас будет встречать {user.maintainer}.\nВаш номер рейса: {flight_number}"
    return pattern

def get_departure_user(user_id):
    
    user = df[df['telegram_id'] == user_id].squeeze().T
    if not type(user.departure) is str:
        pattern = 'Нету данных по отъезду'
    else:
        city, airport, arrival_time, flight_number = user.departure.split(',')
        pattern = f"{user.name_user}, Вы уезжаете в город {city}, {airport} в {arrival_time}.\nВаш номер рейса: {flight_number}"
    return pattern

def get_hotel_user(user_id):
    
    user = df[df['telegram_id'] == user_id].squeeze().T
    if not type(user.hotel) is str:
        pattern = 'Нету данных по проживанию'
    else:
        pattern = f"{user.name_user}, Вы проживаете в гостинице {user.hotel}"
    return pattern


@bot.message_handler(commands=['edit'])
def handle_edit(message):
    user_id = message.from_user.id
    if is_user_authorized(user_id):
        markup = types.InlineKeyboardMarkup(row_width=3)
        button1 = types.InlineKeyboardButton("По приезду", callback_data="edit-arrival")
        button2 = types.InlineKeyboardButton("По отъезду", callback_data="edit-departure")
        markup.add(button1, button2)
        bot.send_message(message.chat.id, "Какую информацию хотите направить?", reply_markup=markup)
    else:
        bot.send_message(user_id,
                         "Вы не авторизованы. Пожалуйста, авторизуйтесь сначала. /authorize")


@bot.callback_query_handler(func=lambda call: call.data.startswith('edit'))
def query_handler_edit(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    if call.data == "edit-arrival":
        msg = bot.send_message(call.message.chat.id,"Введите данные по приезду\nВводить строго по образцу: Город,Аэропорт,Дата и время, Номер рейса\nПример: Уфа,Аэропорт 'Уфимский',10.04.2024 16:22,S9-5046")
        bot.register_next_step_handler(msg, edit_arrival_user)
    elif call.data == "edit-departure":
        msg = bot.send_message(call.message.chat.id,"Введите данные по отъезду\nВводить строго по образцу: Город,Аэропорт,Дата и время, Номер рейса\nПример: Уфа,Аэропорт 'Уфимский',10.04.2024 16:22,S9-5046")
        bot.register_next_step_handler(msg, edit_departure_user)
    
    bot.answer_callback_query(callback_query_id=call.id)


def edit_arrival_user(message):
    user_id = message.from_user.id
    data = message.text
    
    # validate
    try:
        if len(data.split(',')) == 4:
            df.loc[df["telegram_id"]==user_id, 'arrival'] = data
            update_df(df)
        else:
            msg = bot.send_message(message.chat.id,"Неправильный формат. Попробуйте снова.\n")
            bot.register_next_step_handler(msg, edit_arrival_user)
    except:
        msg = bot.send_message(message.chat.id,"Произошла ошибка. Попробуйте снова.\n")
        bot.register_next_step_handler(msg, edit_arrival_user)

def edit_departure_user(message):
    user_id = message.from_user.id
    data = message.text
    
    # validate
    try:
        if len(data.split(',')) == 4:
            df.loc[df["telegram_id"]==user_id, 'departure'] = data
            update_df(df)
        else:
            msg = bot.send_message(message.chat.id,"Неправильный формат. Попробуйте снова.\n")
            bot.register_next_step_handler(msg, edit_departure_user)
    except:
        msg = bot.send_message(message.chat.id,"Произошла ошибка. Попробуйте снова.\n")
        bot.register_next_step_handler(msg, edit_departure_user)


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    if is_user_authorized(message.from_user.id):
        bot.send_message(message.chat.id,
                         """
                         Такой команды у меня нет.\nВоспользуйтесь меню -> /menu
                         """)
    else:
        bot.send_message(message.chat.id,
                         "Вы не авторизованы. Пожалуйста, авторизуйтесь сначала. /authorize")


# Запуск бота
bot.polling(none_stop=True)
