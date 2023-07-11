import os

from dotenv import load_dotenv
from datetime import datetime, date, timedelta
from telebot import TeleBot, types
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

from validator import valid_date, message_to_task
from sql_requests import *


load_dotenv()
token = os.getenv('TOKEN')

bot = TeleBot(token)
today = date.strftime(date.today(), '%d.%m.%Y')

command_messages = ('Все задачи', 'Дела на сегодня', 'Добавить задачу',
                    'Удалить задачу', 'Составить cписок покупок')  # 'Переместить задачу',
n = 0


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
    create_db(message)
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton('Все задачи')
    item2 = types.KeyboardButton('Дела на сегодня')
    item3 = types.KeyboardButton('Добавить задачу')
    item4 = types.KeyboardButton('Удалить задачу')
    item5 = types.KeyboardButton('Составить cписок покупок')
    markup.add(item1, item2, item3, item4, item5)
    text = f'Привет, {message.chat.first_name}' if message.chat.first_name else 'Привет'
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(commands=['add'])
def add(message):
    create_db(message)
    dt, task = valid_date(message.text), message_to_task(message.text.strip('/add'))
    if 'вместе с задачей' in dt:
        global n
        n += 1
        if n < 3:
            bot.send_message(message.chat.id, dt)
            bot.register_next_step_handler(message, add)
        else:
            n = 0
            bot.send_message(message.chat.id, 'Что-то пошло не так, попробуйте другую команду')

    else:
        n = 0
        insert_task_db(message, task, dt)
        bot.send_message(message.chat.id, f'Задача "{task}" добавлена на {dt}')


@bot.message_handler(commands=['show'])
def show(message):
    try:
        date = valid_date(message.text.split()[1].lower())
        text = 'На эту дату нет задач'
        res = [task[0] for task in select_today(message, date)]
        if res:
            text = '\n'.join([f"🔹{v}" for v in res])
        bot.send_message(message.chat.id, text)
    except:
        bot.send_message(message.chat.id, 'Укажите на какую дату показать список задач')


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
            tasks_today(message)
        if message.text == 'Все задачи':
            show_all(message)
        if message.text == 'Удалить задачу':
            bot.send_message(message.chat.id, 'напишите задачу, которую надо удалить')
            bot.register_next_step_handler(message, remove)


@bot.message_handler(commands=['all'])
def show_all(message):
    tasks = {}
    for dt, task in sorted(select_all(message), key=lambda x: datetime.strptime(x[0], '%d.%m.%Y')):
        if datetime.strptime(dt, '%d.%m.%Y') < datetime.today() - timedelta(days=1):
            delete_task(message, task)
        else:
            tasks.setdefault(dt, []).append(task)
    if not tasks:
        text = 'Нет предстоящих задач'
    else:
        text = '\n\n'.join([day + ':\n' + '\n'.join([f"🔹{d}" for d in tasks[day]]) for day in tasks])
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['remove'])
def remove(message):
    task = message_to_task(message.text.strip('/remove'))
    try:
        delete_task(message, task)
        text = f'Задача "{task}" удалена'
    except:
        text = f'Задача "{task}" не найдена'

    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['move'])
def move(message):
    task, date = message_to_task(message.text.stpip('/move')), valid_date(message.text)
    try:
        delete_task(message, task)
        insert_task_db(message, task=task, date=date)
        text = f'Задача "{task}" перемещена на {date}'
    except:
        text = f'Задача "{task}" не найдена'
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
    create_db(message, shop=True)
    for item in items:
        insert_task_db(message, shop=True, item_name=item)
    bot.send_message(message.chat.id, 'Список покупок', reply_markup=make_buttons(items))


@bot.message_handler(commands=['today'])
def tasks_today(message):
    tasks_today = [task[0] for task in select_today(message, today)]
    if tasks_today:
        bot.send_message(message.chat.id, 'Список дел на сегодня:', reply_markup=make_buttons(tasks_today))
    else:
        bot.send_message(message.chat.id, 'На сегодня дел нет, отдыхайте 😉')


@bot.callback_query_handler(lambda c: True)
def answer(call):  # : types.callback_query
    if call.message.text == 'Список покупок':
        update_tasks(call.message, call.data, shop=True)
        item_list = [item[0] for item in select_today(call.message, shop=True)]
        replay = make_buttons(item_list)
        if len(item_list) != 0 and len(tuple(filter(lambda x: '✅' in x, item_list))) == len(item_list):
            bot.answer_callback_query(call.id, text='Вы завершили покупку', show_alert=True)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text='Покупка завершена')
            delete_items(call.message, item_list)
            return
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text='Список покупок',
                              reply_markup=replay, parse_mode='MarkdownV2')

    elif call.message.text == 'Список дел на сегодня:':
        update_tasks(call.message, call.data, today)
        today_tasks = [task[0] for task in select_today(call.message, today)]
        replay = make_buttons(today_tasks)
        if len(today_tasks) != 0 and len(tuple(filter(lambda x: '✅' in x, today_tasks))) == len(today_tasks):
            bot.answer_callback_query(call.id, text='Вы выполнили все дела на сегодня', show_alert=True)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text='Список дел завершен')
            return
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text='Список дел на сегодня:',
                              reply_markup=replay, parse_mode='MarkdownV2')


if __name__ == '__main__':
    # постоянно обращается к серверам телеграм
    bot.polling(none_stop=True)




