"""
Первая версия телеграм бота для тех. поддержки VisiologySupport_bot
Функционал:
- Авторизация по FreshDesk api
- Создание тикета через ввод (клике) команд
- Пропуск почты, замена на telegram@visiology.su
"""


import telebot

from freshdesk.api import API
import datetime as dt

today_date = dt.datetime.today().strftime('%Y.%m.%d %H:%M')

access_token = '1862714973:AAGwGQFpFeiV3SIRLvws7sPY_n2lzBK6s1U'

bot = telebot.TeleBot(access_token)

user_dict = {}
ticket_dict = {}


class Ticket:
    def __init__(self, email):
        self.subject = 'Телеграм ' + today_date
        self.tags = ['Telegram']
        self.email = email
        self.description = None


class User:
    def __init__(self, api):
        self.api = api
        self.is_auth = False


@bot.message_handler(commands=['start'])
def first_welcome(message):
    bot.reply_to(message, "Здравствуйте, сэр!\nВведите свой api ключ")

    bot.register_next_step_handler(message, get_api)


def get_api(message):
    chat_id = message.chat.id
    api = message.text

    user = User(api)
    user_dict[chat_id] = user

    try:
        a = API('newaccount1624950159366.freshdesk.com', user.api)
        a.tickets.list_tickets()

        user.is_auth = True
        bot.send_message(message.from_user.id,
                         'Авторизация прошла успешно, введите команду /create, чтобы создать тикет')
    except:

        user.is_auth = False
        bot.send_message(message.from_user.id, 'Неправильно, введите api заново')
        bot.register_next_step_handler(message, get_api)


@bot.message_handler(commands=['create'])
def ticket_create(message):
    chat_id = message.chat.id
    try:
        user = user_dict[chat_id]
        if message.text == '/create':
            if user.is_auth:
                bot.send_message(message.from_user.id, 'Введите почту клиента')
                bot.register_next_step_handler(message, get_email)
            else:
                bot.send_message(message.from_user.id, 'Сначала авторизуйтесь с помощью команды /start')
    except:
        bot.send_message(message.from_user.id, 'Сначала авторизуйтесь с помощью команды /start')


def get_email(message):
    try:
        chat_id = message.chat.id
        email = message.text

        if email == '/skip':
            email = 'telegram@visiology.su'

        ticket = Ticket(email)
        ticket_dict[chat_id] = ticket

        bot.send_message(message.from_user.id, 'Введите описание тикета')
        bot.register_next_step_handler(message, get_description)
    except:
        bot.reply_to(message, 'Почта введена неверно')


def get_description(message):
    chat_id = message.chat.id
    description = message.text

    user = user_dict[chat_id]
    ticket = ticket_dict[chat_id]

    ticket.description = description
    try:
        a = API('newaccount1624950159366.freshdesk.com', user.api)
        create_ticket = a.tickets.create_ticket(ticket.subject,
                                                email=ticket.email,
                                                description=ticket.description,
                                                tags=ticket.tags)
        bot.send_message(message.from_user.id, 'Тикет создан удачно')
    except Exception:
        bot.send_message(message.from_user.id, 'Упс, что-то пошло не так. Попробуйте создать тикет заново: /create')


bot.polling(none_stop=True)
