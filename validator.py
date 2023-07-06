from datetime import date, datetime, timedelta
import re


def valid_date(text):
    if 'сегодня' in text.lower():
        return date.strftime(date.today(), '%d.%m.%Y')
    elif 'завтра' in text.lower():
        return date.strftime(datetime.today() + timedelta(days=1), '%d.%m.%Y')
    elif 'послезавтра' in text.lower():
        return date.strftime(datetime.today() + timedelta(days=2), '%d.%m.%Y')

    find_date = [re.sub(r'[,/-]', '.', day) for day in re.findall(r'\d{1,2}.\d{1,2}.?\d{0,4}', text)]
    for pattern in (r'%d.%m.%y', r'%d.%m.%Y'):
        try:
            return date.strftime(datetime.strptime(find_date[0].strip(), pattern), '%d.%m.%Y')
        except ValueError:
            continue
        except IndexError:
            return 'вместе с задачей необходимо указать дату, когда нужно ее выполнить, попробуйте еще раз'
    try:
        return date.strftime(datetime.strptime(find_date[0].strip(), r'%d.%m'), '%d.%m.2023')
    except (ValueError, IndexError):
        return 'вместе с задачей необходимо указать дату, когда нужно ее выполнить, попробуйте еще раз'


def message_to_task(text):
    for day in ('сегодня', 'послезавтра', 'завтра'):
        if day in text.lower():
            text = re.sub(day, '', text, count=1, flags=re.I).strip()
    task = re.sub(r'\d{1,2}.\d{1,2}.?\d{0,4}\s*', '', text, count=1, flags=re.I)
    return task.strip()


if __name__ == '__main__':
    a = "Дата начисления 21.04 Дата начисления 21/04/2021 7-1-2000"
    # print(valid_date(a))
    dt = date(day=1, month=1, year=2023)
    mess = 'aaa сегодня'
    print(valid_date(mess), message_to_task(mess))
    # print(datetime.strptime('21.04', '%d.%m'))
    print(type(date.strftime(datetime.strptime('21.04', '%d.%m'), '%d.%m')))
