import os
import logging
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from telebot import TeleBot, types
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

from validator import valid_date, message_to_task
from sql_requests_class import SQLRequests


logging.basicConfig(level=logging.INFO, filename="py_log.log",
                    filemode="a", format="%(asctime)s %(levelname)s %(message)s")

load_dotenv()
token = os.getenv('TOKEN')
bot = TeleBot(token)

command_messages = ('Все задачи', 'Дела на сегодня', 'Добавить задачу',
                    'Удалить задачу', 'Составить cписок покупок')


@bot.message_handler(commands=['help'])
def print_help(message):
    text = {
        '/help': 'вывести список доступных команд',
        '/add <задача дата>': 'добавить задачу в список',
        '/show <дата>': 'показать список задач на конкретную дату',
        '/all': 'показать весь список задач',
        '/remove <задача>': 'удалить конкретную задачу',
        '/move <задача дата>': 'переместить задачу',
        '/shop <список покупок>': 'составить список покупок'
    }
    bot.send_message(message.chat.id, '\n'.join([f"{key} - {val}" for key, val in text.items()]))


@bot.message_handler(commands=['start'])
def start(message):
    req.create_db(message)
    name = message.chat.first_name if message.chat.first_name else ''
    logging.info(f'added user {message.chat.id}, {name} to database')
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton('Все задачи')
    item2 = types.KeyboardButton('Дела на сегодня')
    item3 = types.KeyboardButton('Добавить задачу')
    item4 = types.KeyboardButton('Удалить задачу')
    item5 = types.KeyboardButton('Составить cписок покупок')
    markup.add(item1, item2, item3, item4, item5)
    text = f'Привет, {name}' if name else 'Привет'
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(commands=['add'])
def add(message):
    req.create_db(message)
    dt, task = valid_date(message.text), message_to_task(message.text.strip('/add'))
    if 'вместе с задачей' in dt:
        n = req.select_n(message)
        if n <= 2:
            bot.send_message(message.chat.id, dt)
            req.update_n(message, n + 1)
            bot.register_next_step_handler(message, add)
        else:
            req.update_n(message, 0)
            bot.send_message(message.chat.id, 'Что-то пошло не так, попробуйте другую команду')
            logging.warning(f'ADD: user {message.chat.id} entered the task "{task}" incorrectly several times')
    else:
        req.update_n(message, 0)
        req.insert_task_db(message, task, dt)
        bot.send_message(message.chat.id, f'Задача "{task}" добавлена на {dt}')
        logging.info(f'ADD: user {message.chat.id} added task')


@bot.message_handler(commands=['show'])
def show(message):
    try:
        dt = valid_date(message.text.split()[1].lower())
        text = 'На эту дату нет задач'
        res = [task[0] for task in req.select_today(message, dt)]
        if res:
            text = '\n'.join([f"🔹{v}" for v in res])
        bot.send_message(message.chat.id, text)
    except Exception as err:
        bot.send_message(message.chat.id, 'Укажите на какую дату показать список задач')
        logging.error(f'SHOW: the user {message.chat.id} did not specify a date, error: {err}')


@bot.message_handler(func=lambda m: m.text in command_messages)
def bot_message(message):
    if message.chat.type == 'private':
        if message.text == 'Составить cписок покупок':
            bot.send_message(message.chat.id, 'напишите список')
            bot.register_next_step_handler(message, shop)
        if message.text == 'Добавить задачу':
            bot.send_message(message.chat.id, 'напишите задачу и дату, когда ее надо выполнить')
            bot.register_next_step_handler(message, add)
        if message.text == 'Дела на сегодня':
            todo_today(message)
        if message.text == 'Все задачи':
            show_all(message)
        if message.text == 'Удалить задачу':
            bot.send_message(message.chat.id, 'напишите задачу, которую надо удалить')
            bot.register_next_step_handler(message, remove)


@bot.message_handler(commands=['all'])
def show_all(message):
    tasks = {}
    for dt, task in sorted(req.select_all(message), key=lambda x: datetime.strptime(x[0], '%d.%m.%Y')):
        if datetime.strptime(dt, '%d.%m.%Y') < datetime.today() - timedelta(days=1):
            req.delete_task(message, task)
        else:
            tasks.setdefault(dt, []).append(task)
    if not tasks:
        text = 'Нет предстоящих задач'
    else:
        text = '\n\n'.join([day + ':\n' + '\n'.join([f"🔹{d}" for d in tasks[day]]) for day in tasks])
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['remove'])
def remove(message):
    task = message.text.strip('/remove')
    if req.select_task(message, task):
        req.delete_task(message, task)
        text = f'Задача "{task}" удалена'
        logging.info(f'REMOVE: user {message.chat.id} remove task "{task}"')
    else:
        text = f'Задача "{task}" не найдена'
        logging.error(f'REMOVE: user {message.chat.id}, task "{task}" not found')
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['move'])
def move(message):
    task, dt = message_to_task(message.text.strip('/move')), valid_date(message.text)
    if req.select_task(message, task):
        req.delete_task(message, task)
        req.insert_task_db(message, task=task, date=dt)
        text = f'Задача "{task}" перемещена на {dt}'
        logging.info(f'MOVE: user {message.chat.id} move task "{task}" to date {dt}')
    else:
        text = f'Задача "{task}" не найдена'
        logging.error(f'MOVE: user {message.chat.id}, task "{task}" not found')
    bot.send_message(message.chat.id, text)


def make_buttons(data: list):
    markup = InlineKeyboardMarkup()
    button_list = list(InlineKeyboardButton(text=item, callback_data=f'{item}') for item in data)
    for but in button_list:
        markup.add(but)
    return markup


@bot.message_handler(commands=['shop'])
def shop(message):  # types.Message
    items = message.text.strip('/shop').strip(' ,.!-?/*').split(", ") if ',' in message.text \
        else message.text.strip('/shop').strip(' ,.!-?/*').split()
    req.create_db(message, shop=True)
    for item in items:
        req.insert_task_db(message, shop=True, item_name=item)
    bot.send_message(message.chat.id, 'Список покупок', reply_markup=make_buttons(items))
    logging.info(f'the user {message.chat.id} made a shopping list')


@bot.message_handler(commands=['today'])
def todo_today(message):
    tasks_today = [task[0] for task in req.select_today(message, date.strftime(date.today(), '%d.%m.%Y'))]
    print(tasks_today)
    if tasks_today:
        bot.send_message(message.chat.id, 'Список дел на сегодня:', reply_markup=make_buttons(tasks_today))
    else:
        bot.send_message(message.chat.id, 'На сегодня дел нет, отдыхайте 😉')


@bot.callback_query_handler(lambda c: True)
def answer(call):  # : types.callback_query
    if call.message.text == 'Список покупок':
        req.update_tasks(call.message, call.data, shop=True)
        item_list = [item[0] for item in req.select_today(call.message, shop=True)]
        replay = make_buttons(item_list)
        if len(item_list) != 0 and len(tuple(filter(lambda x: '✅' in x, item_list))) == len(item_list):
            bot.answer_callback_query(call.id, text='Вы завершили покупку', show_alert=True)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text='Покупка завершена')
            req.delete_items(call.message, item_list)
            logging.info(f'user {call.message.chat.id} closed shopping list')
            return
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text='Список покупок',
                              reply_markup=replay, parse_mode='MarkdownV2')

    elif call.message.text == 'Список дел на сегодня:':
        istoday = date.strftime(date.today(), '%d.%m.%Y')
        req.update_tasks(call.message, call.data, istoday)
        today_tasks = [task[0] for task in req.select_today(call.message, istoday)]
        replay = make_buttons(today_tasks)
        if len(today_tasks) != 0 and len(tuple(filter(lambda x: '✅' in x, today_tasks))) == len(today_tasks):
            bot.answer_callback_query(call.id, text='Вы выполнили все дела на сегодня', show_alert=True)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text='Список дел завершен')
            return
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text='Список дел на сегодня:',
                              reply_markup=replay, parse_mode='MarkdownV2')


if __name__ == '__main__':
    # постоянно обращается к серверам телеграм
    req = SQLRequests()
    try:
        bot.polling(none_stop=True)
        logging.info(f'successful authorization')
    except Exception as err:
        logging.critical(f'authorization failed, error{err}')
