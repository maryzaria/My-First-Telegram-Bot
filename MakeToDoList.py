import sys


class MakeToDoList:
    def __init__(self) -> None:
        self.tasks = {}

    def __repr__(self) -> str:
        if not self.tasks:
            return 'Нет предстоящих задач'
        return '\n'.join([key + ':\n' + self.show_tasks_on_date(key) for key, val in self.tasks.items()])

    def add_task(self, task: str, date: str) -> str:
        self.tasks.setdefault(date, []).append(task)
        return f'Задача "{task}" добавлена на {date}'

    def show_tasks_on_date(self, date: str) -> str:
        res = self.tasks.get(date, 'На эту дату нет задач')
        if isinstance(res, list):
            res = '\n'.join([f"- {v}" for v in res])
        return res

    def remove_all(self) -> str:
        self.tasks.clear()
        return 'Все задачи удалены'

    def remove_task(self, date: str, task: str) -> str:
        if task in self.tasks[date]:
            self.tasks[date].remove(task)
            return 'Задача удалена'
        return 'Задача не найдена'

    def move_task(self, task: str, new_date: str) -> str:
        for old_date, tasks in self.tasks.items():
            if task in tasks:
                self.remove_task(old_date, task)
                self.add_task(task, new_date)
                return f'Задача "{task}" перемещена на {new_date}'


def show_help():
    lst = {
        'help': 'напечатать справку по программе',
        'add': 'добавить задачу в список',
        'show': 'показать список задач на конкретную дату',
        'show all': 'показать весь список задач',
        'remove': 'удалить конкретную задачу',
        'remove all': 'удалить все задачи',
        'exit': 'выход/завершение работы'
    }
    return '\n'.join([f"{key} - {val}" for key, val in lst.items()])


if __name__ == '__main__':
    example = MakeToDoList()
    print("Введите команду: ")
    for command in sys.stdin:
        # print(eval(f'example.{command.strip()}()'))
        command = command.strip()
        if command == "help":
            print(show_help())
        elif command == "show all":
            print(example)
        elif command == "show":
            dt = input('Введите дату: ')
            print(example.show_tasks_on_date(dt))
        elif command == "add":
            item = str(input("Введите название задачи: ")).strip()
            dt = str(input('Введите дату: ')).lower()
            print(example.add_task(item, dt))
        elif command == 'remove all':
            print(example.remove_all())
        elif command == 'remove':
            dt = str(input('Введите дату: ')).lower()
            task = str(input("Введите задачу: ")).strip()
            print(example.remove_task(dt, task))
        elif command == 'remove':
            item = str(input("Введите задачу: ")).strip()
            dt = str(input('Введите новую дату: ')).lower()
            print(example.move_task(item, dt))
        elif command == 'exit':
            break
        else:
            print("Неизвестная команда")
            break

    print("До свидания!")

# d = {'31.12': ['2022', '2023'], '30.12': ['2021', '2020']}
# print('\n'.join([key + ':\n' + '\n'.join([f"- {v}" for v in val]) for key, val in d.items()]))
