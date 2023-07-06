import os
from dotenv import load_dotenv
from telebot import TeleBot, types


from validator import valid_date, message_to_task
from buttons import make_buttons, new_items, new_tasks


load_dotenv()
token = os.getenv('TOKEN')

bot = TeleBot(token)

tasks = {}
item_list = []


@bot.message_handler(commands=['help'])
def print_help(message):
    text = {
        '/help': 'вывести список доступных команд',
        '/add <задача дата>': 'добавить задачу в список',
        '/show <дата>': 'показать список задач на конкретную дату',
        '/all': 'показать весь список задач',
        '/remove <задача>': 'удалить конкретную задачу',
        '/clear': 'удалить все задачи',
        '/move <задача дата>': 'переместить задачу',
        '/shop <список покупок>': 'составить список покупок'
    }
    bot.send_message(message.chat.id, '\n'.join([f"{key} - {val}" for key, val in text.items()]))


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item2 = types.KeyboardButton('Все задачи')
    item3 = types.KeyboardButton('Дела на сегодня')
    item4 = types.KeyboardButton('Добавить задачу')
    item5 = types.KeyboardButton('Составить cписок покупок')
    markup.add(item2, item3, item4, item5)
    bot.send_message(message.chat.id, f'Привет, {message.chat.first_name}', reply_markup=markup)


@bot.message_handler(commands=['add'])
def add(message):
    dt, task = valid_date(message.text), message_to_task(message.text.strip('/add'))
    if 'попробуйте еще раз' in dt:
        bot.send_message(message.chat.id, dt)
    else:
        tasks.setdefault(dt, []).append(task)
        bot.send_message(message.chat.id, f'Задача "{task}" добавлена на {dt}')


@bot.message_handler(commands=['show'])
def show(message):
    try:
        date = valid_date(message.text.split()[1].lower())
        text = tasks.get(date, 'На эту дату нет задач')
        if isinstance(text, list):
            text = '\n'.join([f"🔹{v}" for v in text])
        bot.send_message(message.chat.id, text)
    except IndexError:
        bot.send_message(message.chat.id, 'укажите, на какую дату показать список задач')


@bot.message_handler(func=lambda m: m.text in ('Составить cписок покупок', 'Дела на сегодня', 'Все задачи', 'Добавить задачу'))
def bot_message(message):
    if message.chat.type == 'private':
        if message.text == 'Составить cписок покупок':
            bot.send_message(message.chat.id, 'напишите список продуктов')
            bot.register_next_step_handler(message, shop)
        if message.text == 'Добавить задачу':
            bot.send_message(message.chat.id, 'напишите задачу и дату, когда ее надо выполнить')
            bot.register_next_step_handler(message, add)
        if message.text == 'Дела на сегодня':
            tasks_today(message)
        if message.text == 'Все задачи':
            show_all(message)


@bot.message_handler(commands=['all'])
def show_all(message):
    if not tasks:
        text = 'Нет предстоящих задач'
    else:
        text = '\n'.join([str(day) + ':\n' + '\n'.join([f"🔹{d}" for d in tasks[day]]) for day in tasks])
    print(text)
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['remove'])
def remove(message):
    task = message.text.split(maxsplit=1)[1]
    print(task)
    text = f'Задача "{task}" не найдена'
    for items in tasks.values():
        if task in items:
            items.remove(task)
            text = f'Задача "{task}" удалена'
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['clear'])
def clear(message):
    tasks.clear()
    bot.send_message(message.chat.id, 'Все задачи удалены')


@bot.message_handler(commands=['move'])
def move(message):
    task, date = message_to_task(message.text.stpip('/move')), valid_date(message.text)
    text = f'Задача "{task}" не найдена'
    for old_date, items in tasks.items():
        if task in items:
            items.remove(task)
            text = f'Задача "{task}" перемещена на {date}'
    tasks.setdefault(date, []).append(task)
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['shop'])
def shop(message):  # types.Message
    items = message.text.strip('/shop').split(",") if ',' in message.text else message.text.strip('/shop').split()
    item_list.clear()
    item_list.extend(items)
    bot.send_message(message.chat.id, 'Список покупок', reply_markup=make_buttons(items))


@bot.message_handler(commands=['today'])
def tasks_today(message):
    today = valid_date('сегодня')
    if today in tasks:
        bot.send_message(message.chat.id, 'Список дел на сегодня', reply_markup=make_buttons(tasks[today]))
    else:
        bot.send_message(message.chat.id, 'На сегодня дел нет, отдыхайте 😉')


@bot.callback_query_handler(lambda c: True)  # lambda c: c.data == 'butt_id'
def answer(call):  # : types.callback_query
    if call.message.text == 'Список покупок':
        replay = new_items(call.data, item_list)
        if len(item_list) != 0 and len(tuple(filter(lambda x: '✅' in x, item_list))) == len(item_list):
            bot.answer_callback_query(call.id, text='Вы завершили покупку', show_alert=True)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text='Покупка завершена')
            return
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text='Список покупок',
                              reply_markup=replay, parse_mode='MarkdownV2')

    elif call.message.text == 'Список дел на сегодня':
        today_tasks = tasks[valid_date('сегодня')]
        replay = new_tasks(call.data, today_tasks)
        if len(today_tasks) != 0 and len(tuple(filter(lambda x: 'ВЫПОЛНЕНО' in x, today_tasks))) == len(today_tasks):
            bot.answer_callback_query(call.id, text='Вы выполнили все дела на сегодня', show_alert=True)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text='Список дел завершен')
            return
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text='Список дел на сегодня',
                              reply_markup=replay, parse_mode='MarkdownV2')


if __name__ == '__main__':
    # постоянно обращается к серверам телеграм
    bot.polling(none_stop=True)



