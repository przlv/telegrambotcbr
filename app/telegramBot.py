import telebot
import pandas as pd
from telebot import types
from config import SECRET_CODE
from typing import List
from app.patterns import create_keyboard_menu


class TelegramBot:
    
    
    def __init__(self, token: str) -> None:
        self.token = token
        self.bot = telebot.TeleBot(token)
        self.df: pd.DataFrame = self.load_data()
        self.authorized_users: List[int] = self.load_authorized_users()
        self.initialize_handlers()
        self.initialize_callbacks()
        print('..::Bot connected::..')
        
            
    def is_user_authorized(self, user_id: int) -> bool:
        return user_id in self.authorized_users
    
    
    def initialize_handlers(self) -> None:
        
        @self.bot.message_handler(commands=['start'])
        def handle_welcome(message):
            if self.is_user_authorized(message.from_user.id):
                markup = create_keyboard_menu()
                self.bot.send_message(message.chat.id, "Выберите опцию:", reply_markup=markup)
            else:
                self.bot.send_message(message.chat.id, "Вы не авторизованы. Пожалуйста, авторизуйтесь сначала. /authorize")
        
        @self.bot.message_handler(commands=['authorize'])
        def handle_register(message):
            if self.is_user_authorized(message.from_user.id):
                self.bot.send_message(message.chat.id, 'Вы уже авторизированы')
            else:
                msg = self.bot.send_message(message.chat.id,"Введите секретный код для регистрации")
                self.bot.register_next_step_handler(msg, self.check_secret_key)
        
        @self.bot.message_handler(commands=['menu'])
        def handle_menu(message):
            user_id = message.from_user.id
            if self.is_user_authorized(user_id):
                markup = create_keyboard_menu()
                self.bot.send_message(message.chat.id, "Выберите опцию:", reply_markup=markup)
            else:
                self.bot.send_message(user_id,
                                "Вы не авторизованы. Пожалуйста, авторизуйтесь сначала. /authorize")

        @self.bot.message_handler(func=lambda message: True)
        def echo_all(message):
            if self.is_user_authorized(message.from_user.id):
                self.bot.send_message(message.chat.id,
                                """
                                Такой команды у меня нет.\nВоспользуйтесь меню -> /menu
                                """)
            else:
                self.bot.send_message(message.chat.id,
                                "Вы не авторизованы. Пожалуйста, авторизуйтесь сначала. /authorize")


    def initialize_callbacks(self)-> None:
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('get'))
        def query_handler_get(call):
            user_id = call.from_user.id
            chat_id = call.message.chat.id

            if call.data == "get-arrival":
                response = self.get_arrival_user(user_id)
            elif call.data == "get-departure":
                response = self.get_departure_user(user_id)
            elif call.data == "get-hotel":
                response = self.get_hotel_user(user_id)
            
            self.bot.answer_callback_query(callback_query_id=call.id)
            if response == call.message.text:
                return
            
            markup = create_keyboard_menu()
            try:
                self.bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=response, reply_markup=markup)
            except telebot.apihelper.ApiTelegramException:
                self.bot.send_message(chat_id, response, reply_markup=markup)


    def load_data(self) -> pd.DataFrame:
        try:
            return pd.read_excel('./data/data.xlsx')
        except Exception as e:
            print('Error loading data\n', e)
    
    
    def load_authorized_users(self) -> List[int]:
        authorized_users: List[int] = []
        for user in self.df.itertuples():
            if user.telegram_id != -1:
                authorized_users.append(user.telegram_id)
        return authorized_users
    
    
    def update_excel_spreadsheet(self) -> bool:
        try:
            self.df.to_excel('./data/data.xlsx', index=False)
            return True
        except Exception as e:
            print('Error updating', e)
            return False

    
    def add_user(self, user_id: int, username: str) -> bool:
        try:
            index = self.df.index[self.df['name_user'].str.lower() == username]
            self.df.loc[index, 'telegram_id'] = user_id
            self.update_excel_spreadsheet()
            return True
        except:
            return False
        
    
    def check_secret_key(self, message: types.Message) -> None:
        if message.text == SECRET_CODE:
            msg = self.bot.send_message(message.chat.id, "Секретный код верен. Введите ваше в формате Имя Фамилия (Пример: Иван Иванов).")
            self.bot.register_next_step_handler(msg, self.process_register_step)
        else:
            self.bot.send_message(message.chat.id, "Неверный секретный код.")
        
    
    def process_register_step(self, message: types.Message) -> None:
        try:
            user_id = message.from_user.id
            username= message.text
            responce = self.register_user(user_id, username)
            if responce == 'user_added':
                self.bot.reply_to(message, "Вы успешно зарегистрированы!")
            elif responce == 'user_already_authorized':
                self.bot.reply_to(message, "Вы уже зарегистрированы.")
            else:
                self.bot.reply_to(message, f"Такого сотрудника нет: {message.text}\nПопробуйте ещераз")
                msg = self.bot.send_message(message.chat.id, "Введите ваше ФИО в формате < Имя Фамилия > (Пример: Иван Иванов).")
                self.bot.register_next_step_handler(msg, self.process_register_step)
        except Exception as e:
            self.bot.reply_to(message, 'Ошибка при регистрации.')
            print(e)
    
    
    def register_user(self, user_id: int, username: str) -> str:
        username = username.strip().lower()
        user = self.df[self.df['name_user'].str.lower() == username].squeeze().T
        if not user.empty:
            if user.telegram_id == -1:
                self.add_user(user_id, username)
                self.authorized_users.append(user_id)
                return 'user_added'
            else:
                return 'user_already_authorized'
        else:
            return 'user_not_found'
    
    
    def get_arrival_user(self, user_id: int) -> str:
    
        user = self.df[self.df['telegram_id'] == user_id].squeeze().T
        if not type(user.arrival) is str:
            pattern = 'Нету данных по прибытию'
        else:
            city, airport, arrival_time, flight_number = user.arrival.split(',')
            pattern = f"{user.name_user}, Вы прибываете в город {city}, {airport} в {arrival_time}.\nВас будет встречать {user.maintainer}.\nВаш номер рейса: {flight_number}"
        return pattern
    
    
    def get_departure_user(self, user_id: int) -> str:
    
        user = self.df[self.df['telegram_id'] == user_id].squeeze().T
        if not type(user.departure) is str:
            pattern = 'Нету данных по отъезду'
        else:
            city, airport, arrival_time, flight_number = user.departure.split(',')
            pattern = f"{user.name_user}, Вы уезжаете в город {city}, {airport} в {arrival_time}.\nВаш номер рейса: {flight_number}"
        return pattern


    def get_hotel_user(self, user_id: int) -> str:
        
        user = self.df[self.df['telegram_id'] == user_id].squeeze().T
        if not type(user.hotel) is str:
            pattern = 'Нету данных по проживанию'
        else:
            pattern = f"{user.name_user}, Вы проживаете в гостинице {user.hotel}"
        return pattern
    
    
    def run(self) -> None:
        self.bot.polling(none_stop=True)
    