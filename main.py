import telebot
from telebot import types
import re
import sqlite3

bot = telebot.TeleBot('7042795140:AAFdZluOWc_fG4ejufKr8LZ4yppKnWYmDi8')

# Подключение к базе данных
conn = sqlite3.connect('accounts.db', check_same_thread=False)
cursor = conn.cursor()

# Регистрация и авторизация
user_login = {}
user_mail = {}
user_password = {}
registration_state = {}
authorization_state = {}
used_start_command = {}


# Проверка почты
def is_valid_email(email):
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None


def upsert_user(user_id, login, email, password, registration_state, authorization_state, language):
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, login, email, password, registration_state, authorization_state, language)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, login, email, password, registration_state, authorization_state, language))
    conn.commit()


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if used_start_command.get(user_id):
        bot.send_message(message.chat.id,
                         'Вы уже начали взаимодействие с ботом. Напишите /help для взаимодействия с ботом.')
        return

    used_start_command[user_id] = True
    greeting = '<b>Здравствуйте. Общие команды вы можете узнать при помощи /help</b>'
    markup = types.InlineKeyboardMarkup()
    btn_reg = types.InlineKeyboardButton("Регистрация", callback_data='btn_reg')
    btn_auto = types.InlineKeyboardButton("Авторизация", callback_data='btn_auto')
    markup.add(btn_reg, btn_auto)
    bot.send_message(message.chat.id, greeting, parse_mode="HTML", reply_markup=markup)


@bot.message_handler(commands=['help'])
def help_commands(message):
    markup = types.InlineKeyboardMarkup()
    btn_reg = types.InlineKeyboardButton("Регистрация", callback_data='btn_reg')
    btn_auto = types.InlineKeyboardButton('Авторизация', callback_data='btn_auto')
    markup.add(btn_reg, btn_auto)
    btn_about_bot = types.InlineKeyboardButton("О боте", callback_data='btn_about_bot')
    btn_about_company = types.InlineKeyboardButton('Компания', callback_data='btn_about_company')
    markup.add(btn_about_bot, btn_about_company)
    btn_asked_questions = types.InlineKeyboardButton('Часто задаваемые вопросы', callback_data='btn_asked_questions')
    markup.add(btn_asked_questions)
    bot.send_message(message.chat.id,
                     'Это раздел основных команд, который будет обновляться по мере разработки бота. Ниже вы можете ознакомиться с доступными функциями.',
                     reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: True)
def callback_message(callback):
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    message_id = callback.message.message_id
    markup = types.InlineKeyboardMarkup()

    if callback.data == 'btn_reg':
        registration_state[user_id] = 'waiting_for_login'
        bot.send_message(chat_id, 'Введите логин:')
        bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)
        bot.delete_message(chat_id, message_id)

    elif callback.data == 'btn_auto':
        authorization_state[user_id] = 'waiting_for_auth_login'
        bot.send_message(chat_id, 'Введите логин для авторизации:')
        bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)
        bot.delete_message(chat_id, message_id)

    elif callback.data == 'btn_about_bot':
        bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                              text="Информация о боте", reply_markup=None)
        bot.delete_message(chat_id, message_id)

    elif callback.data == 'btn_about_company':
        bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                              text="Информация о компании", reply_markup=None)
        bot.delete_message(chat_id, message_id)

    elif callback.data == 'btn_asked_questions':
        bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                              text="Часто задаваемые вопросы", reply_markup=None)
        bot.delete_message(chat_id, message_id)


@bot.message_handler(func=lambda message: registration_state.get(message.from_user.id) == "waiting_for_mail")
def process_mail(message):
    user_id = message.from_user.id
    email = message.text

    if is_valid_email(email):
        user_mail[user_id] = email
        registration_state[user_id] = 'waiting_for_password'
        bot.send_message(message.chat.id, "Введите пароль:")
    else:
        bot.send_message(message.chat.id, "Некорректный формат почты. Пожалуйста, введите правильный email:")


@bot.message_handler(func=lambda message: registration_state.get(message.from_user.id) == 'waiting_for_login')
def process_login(message):
    user_id = message.from_user.id
    user_login[user_id] = message.text
    registration_state[user_id] = 'waiting_for_mail'
    bot.send_message(message.chat.id,'Перед отправкой убедитесь, что вы правильно написали почту. Введите электронную почту:')


@bot.message_handler(func=lambda message: registration_state.get(message.from_user.id) == 'waiting_for_password')
def process_password(message):
    user_id = message.from_user.id
    user_password[user_id] = message.text
    registration_state[user_id] = 'waiting_for_password_confirmation'
    bot.send_message(message.chat.id, 'Подтвердите пароль:')


@bot.message_handler(func=lambda message: registration_state.get(message.from_user.id) == 'waiting_for_password_confirmation')
def confirm_password(message):
    user_id = message.from_user.id
    if user_password.get(user_id) == message.text:
        upsert_user(user_id, user_login.get(user_id), user_mail.get(user_id), message.text,'Done', authorization_state.get(user_id),'en')  # Замените 'en' на нужный язык
        markup = types.InlineKeyboardMarkup()
        btn_auto = types.InlineKeyboardButton("Авторизоваться", callback_data='btn_auto')
        markup.add(btn_auto)

        bot.send_message(message.chat.id, 'Регистрация успешна!', reply_markup=markup)
        registration_state[user_id] = 'Done'
        # Очистка данных
        del user_login[user_id]
        del user_password[user_id]
        del registration_state[user_id]
    else:
        bot.send_message(message.chat.id, 'Пароли не совпадают. Попробуйте снова.')
        registration_state[user_id] = 'waiting_for_password'
        bot.send_message(message.chat.id, 'Введите пароль:')


@bot.message_handler(func=lambda message: authorization_state.get(message.from_user.id) == 'waiting_for_auth_login')
def process_auth_login(message):
    user_id = message.from_user.id
    user_login[user_id] = message.text
    authorization_state[user_id] = "waiting_for_auth_password"
    bot.send_message(message.chat.id, "Введите пароль для авторизации:")


@bot.message_handler(func=lambda message: authorization_state.get(message.from_user.id) == "waiting_for_auth_password")
def process_auth_password(message):
    user_id = message.from_user.id
    cursor.execute('SELECT password FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()

    if row and row[0] == message.text:
        bot.send_message(message.chat.id, "Авторизация прошла успешно!")
        authorization_state[user_id] = 'Done'
        # Обновление состояния в базе данных
        cursor.execute('UPDATE users SET authorization_state = ? WHERE user_id = ?', ('Done', user_id))
        conn.commit()
    else:
        bot.send_message(message.chat.id, "Неверный логин или пароль. Попробуйте снова.")
        authorization_state[user_id] = 'waiting_for_auth_login'
        bot.send_message(message.chat.id, 'Введите логин для авторизации:')


bot.polling(non_stop=True)