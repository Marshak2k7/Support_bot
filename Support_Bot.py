"""
Первая версия телеграм бота для тех. поддержки VisiologySupport_bot
Функционал:
- Авторизация по FreshDesk api
- Создание тикета через ввод (клике) команд
- Пропуск почты, замена на telegram@visiology.su
- Описание тикета принимает несколько сообщений от пользователя
"""

import telebot

from freshdesk.api import API
import datetime as dt


def start_ticket_info_collection(chat_id):
    chat_id_started_collection[chat_id] = True
    chat_id_ticket_collection[chat_id] = []


today_date = dt.datetime.today().strftime('%Y.%m.%d %H:%M')

access_token = '{Your_token}'

bot = telebot.TeleBot(access_token)

user_dict = {}
ticket_dict = {}

chat_id_started_collection = {}
chat_id_ticket_collection = {}


class Ticket:
    def __init__(self, email):
        self.subject = 'Телеграм ' + today_date
        self.tags = ['Telegram']
        self.email = email
        self.description = None

    def create_ticket(self, api):
        ticket = api.tickets.create_ticket(self.subject,
                                           email=self.email,
                                           description=self.description,
                                           tags=self.tags)
        return ticket


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
        a = API('{your_company}.freshdesk.com', user.api)
        a.tickets.list_tickets()

        user.is_auth = True
        bot.send_message(chat_id,
                         'Авторизация прошла успешно, введите команду /create, чтобы создать тикет')
    except:

        user.is_auth = False
        bot.send_message(chat_id, 'Неправильно, введите api заново')
        bot.register_next_step_handler(message, get_api)


@bot.message_handler(commands=['create'])
def ticket_create(message):
    chat_id = message.chat.id
    try:
        user = user_dict[chat_id]
        if message.text == '/create':
            if user.is_auth:
                bot.send_message(chat_id, 'Введите почту клиента или введите команду /skip, чтобы '
                                          'пропустить')
                bot.register_next_step_handler(message, get_email)
            else:
                bot.send_message(chat_id, 'Сначала авторизуйтесь с помощью команды /start')
    except:
        bot.send_message(chat_id, 'Сначала авторизуйтесь с помощью команды /start')


def get_email(message):
    try:
        chat_id = message.chat.id
        email = message.text

        if email == '/skip':
            email = 'telegram@visiology.su'

        ticket = Ticket(email)
        ticket_dict[chat_id] = ticket

        bot.send_message(message.from_user.id, 'Введите описание тикета, а затем выполните команду /stop')

        start_ticket_info_collection(chat_id)
    except:
        bot.reply_to(message, 'Почта введена неверно')


@bot.message_handler(content_types=["text", "photo", "file"])
def process_message(message):
    chat_id = message.chat.id
    if message.text == '/stop':
        stop_collection(message)

    elif chat_id_started_collection.get(chat_id, False):
        description = message.text
        chat_id_ticket_collection[chat_id].append(description)
    else:
        bot.send_message(chat_id, 'Вы кто такие?')


def save_ticket_info(chat_id, ticket_info_text):

    user = user_dict[chat_id]
    ticket = ticket_dict[chat_id]

    ticket.description = ticket_info_text
    try:
        a = API('{your_company}.freshdesk.com', user.api)
        _ = ticket.create_ticket(a)
        bot.send_message(chat_id, 'Тикет создан удачно')
    except Exception:
        bot.send_message(chat_id, 'Упс, что-то пошло не так. Попробуйте создать тикет заново: /create')


@bot.message_handler(commands=['stop'])
def stop_collection(message):
    chat_id = message.chat.id
    chat_id_started_collection[chat_id] = False

    ticket_info_list = chat_id_ticket_collection.get(chat_id, []).copy()
    chat_id_ticket_collection[chat_id] = []

    ticket_info_text = '<br><br>'.join(ticket_info_list)
    if ticket_info_text:
        save_ticket_info(chat_id, ticket_info_text)


bot.polling(none_stop=True)
