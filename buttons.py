from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup


def make_buttons(data: list):
    markup = InlineKeyboardMarkup()
    button_list = list(InlineKeyboardButton(text=item, callback_data=f'{item}') for item in data)
    for but in button_list:
        markup.add(but)
    return markup


def new_items(data, items):
    for index, item in enumerate(items):
        if '✅' in data and item == data:
            old_item = data.strip('✅')
            items.remove(item)
            items.insert(index, old_item)
        elif item == data:
            items.remove(item)
            items.insert(index, f'✅ {data}')
    return make_buttons(items)


def new_tasks(data, tasks_list):
    for index, item in enumerate(tasks_list):
        if 'ВЫПОЛНЕНО' in data and item == data:
            old_task = ' '.join(data.split()[:-1]).strip('✅')
            tasks_list.remove(item)
            tasks_list.insert(index, old_task)
        elif item == data:
            tasks_list.remove(item)
            tasks_list.insert(index, f'✅{data} ВЫПОЛНЕНО')
    return make_buttons(tasks_list)