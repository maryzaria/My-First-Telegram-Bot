import sqlite3


def create_db(message, shop=True):
    conn = sqlite3.connect('user_db.sql')
    cur = conn.cursor()
    # cur.execute("""
    # DROP TABLE user;
    # """)
    # cur.execute("""
    # DROP TABLE task;
    # """)
    # cur.execute("""
    # DROP TABLE shop;
    # """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user (
        id INTEGER PRIMARY KEY,
        chat_id INTEGER UNIQUE NOT NULL,
        username VARCHAR(100),
        first_name VARCHAR(100),
        last_name VARCHAR(100)
    );
    """)
    cur.execute("""
    INSERT INTO user (chat_id, username, first_name, last_name) VALUES (?, ?, ?, ?) ON CONFLICT DO NOTHING;
    """, (message.chat.id, message.chat.username, message.chat.first_name, message.chat.last_name))

    cur.execute("""
    CREATE TABLE IF NOT EXISTS task (
        id INTEGER PRIMARY KEY,
        content text NOT NULL,
        date VARCHAR(15) NOT NULL, 
        chat_id INTEGER REFERENCES user(chat_id)
    );
    """)

    if shop:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS shop (
            id INTEGER PRIMARY KEY,
            item_name VARCHAR(50) NOT NULL, 
            chat_id INTEGER REFERENCES user(chat_id)
            );
            """)
    conn.commit()
    cur.close()
    conn.close()


def insert_task_db(message, task=None, date=None, shop=False, item_name=None):
    conn = sqlite3.connect('user_db.sql')
    cur = conn.cursor()
    if task is not None and date is not None:
        cur.execute("""
        INSERT INTO task (content, date, chat_id) VALUES (?, ?, ?);
        """, (task, date, message.chat.id))
    if shop:
        cur.execute("""
        INSERT INTO shop (item_name, chat_id) VALUES (?, ?);
        """, (item_name, message.chat.id))
    conn.commit()
    cur.close()
    conn.close()


def select_today(message, date=None, shop=False):
    conn = sqlite3.connect('user_db.sql')
    cur = conn.cursor()
    if date:
        cur.execute("""
        SELECT content FROM task 
        WHERE date = ? AND chat_id = ?;
        """, (date, message.chat.id))
    if shop:
        cur.execute("""
        SELECT item_name FROM shop 
        WHERE chat_id = ?;
        """, (message.chat.id,))
    tasks = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    return tasks


def select_all(message):
    conn = sqlite3.connect('user_db.sql')
    cur = conn.cursor()
    cur.execute("""
    SELECT date, content FROM task 
    WHERE chat_id = ?;
    """, (message.chat.id,))
    tasks = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    return tasks


def update_tasks(message, task, date=None, shop=False):
    conn = sqlite3.connect('user_db.sql')
    cur = conn.cursor()
    if not shop:
        if '✅' in task:
            cur.execute("""
            UPDATE task 
            SET content = ?
            WHERE content = ? AND date = ? AND chat_id = ?; 
            """, (task.strip('✅'), task, date, message.chat.id))
        else:
            cur.execute("""
            UPDATE task 
            SET content = ?
            WHERE content = ? AND date = ? AND chat_id = ?; 
            """, ('✅' + task, task, date, message.chat.id))
    else:
        if '✅' in task:
            cur.execute("""
            UPDATE shop 
            SET item_name = ?
            WHERE item_name = ? AND chat_id = ?; 
            """, (task.strip('✅'), task, message.chat.id))
        else:
            cur.execute("""
            UPDATE shop 
            SET item_name = ?
            WHERE item_name = ? AND chat_id = ?; 
            """, ('✅' + task, task, message.chat.id))
    conn.commit()
    cur.close()
    conn.close()


def delete_task(message, task):
    conn = sqlite3.connect('user_db.sql')
    cur = conn.cursor()
    if isinstance(task, str):
        cur.execute("""
        DELETE FROM task WHERE content = ? AND chat_id = ?;
        """, (task, message.chat.id))
    elif isinstance(task, (list, tuple)):
        for t in task:
            cur.execute("""
            DELETE FROM task WHERE content = ? AND chat_id = ?;
            """, (t, message.chat.id))
    conn.commit()
    cur.close()
    conn.close()


def delete_items(message, items):
    conn = sqlite3.connect('user_db.sql')
    cur = conn.cursor()
    for item in items:
        cur.execute("""
        DELETE FROM shop WHERE item_name = ? AND chat_id = ?;
        """, (item, message.chat.id))
    conn.commit()
    cur.close()
    conn.close()
