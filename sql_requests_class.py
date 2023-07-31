import sqlite3


class SQLRequests:
    def __start(self):
        self.conn = sqlite3.connect('user_db.sql')
        self.cur = self.conn.cursor()

    def __close(self):
        self.conn.commit()
        self.cur.close()
        self.conn.close()

    def __drop_table(self):
        self.__start()
        # self.cur.execute("""
        # DROP TABLE user;
        # """)
        # self.cur.execute("""
        # DROP TABLE task;
        # """)
        self.cur.execute("""
        DROP TABLE shop;
        """)
        self.__close()

    def create_db(self, message, shop=True):
        self.__drop_table()
        self.__start()
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY,
            chat_id INTEGER UNIQUE NOT NULL,
            username VARCHAR(100),
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            n INTEGER default 0
        );
        """)
        self.cur.execute("""
        INSERT INTO user (chat_id, username, first_name, last_name) VALUES (?, ?, ?, ?) ON CONFLICT DO NOTHING;
        """, (message.chat.id, message.chat.username, message.chat.first_name, message.chat.last_name))

        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS task (
            id INTEGER PRIMARY KEY,
            content text NOT NULL,
            date VARCHAR(15) NOT NULL, 
            chat_id INTEGER REFERENCES user(chat_id)
        );
        """)

        if shop:
            self.cur.execute("""
            CREATE TABLE IF NOT EXISTS shop (
                id INTEGER PRIMARY KEY,
                item_name VARCHAR(50) NOT NULL, 
                chat_id INTEGER REFERENCES user(chat_id)
                );
                """)
        self.__close()

    def insert_task_db(self, message, task=None, date=None, shop=False, item_name=None):
        self.__start()
        if task is not None and date is not None:
            self.cur.execute("""
            INSERT INTO task (content, date, chat_id) VALUES (?, ?, ?);
            """, (task, date, message.chat.id))
        if shop:
            self.cur.execute("""
            INSERT INTO shop (item_name, chat_id) VALUES (?, ?);
            """, (item_name, message.chat.id))
        self.__close()

    def select_today(self, message, date=None, task=False, shop=False):
        self.__start()
        if task:
            self.cur.execute("""
            SELECT content FROM task 
            WHERE date = ? AND chat_id = ?;
            """, (date, message.chat.id))
        if shop:
            self.cur.execute("""
            SELECT item_name FROM shop 
            WHERE chat_id = ?;
            """, (message.chat.id,))
        tasks = self.cur.fetchall()
        self.__close()
        return tasks

    def select_all(self, message):
        self.__start()
        self.cur.execute("""
        SELECT date, content FROM task 
        WHERE chat_id = ?;
        """, (message.chat.id,))
        tasks = self.cur.fetchall()
        self.__close()
        return tasks

    def select_task(self, message, task):
        self.__start()
        self.cur.execute("""
        SELECT id FROM task 
        WHERE chat_id = ? AND content = ?;
        """, (message.chat.id, task))
        task_id = self.cur.fetchone()
        self.__close()
        return task_id

    def select_n(self, message):
        self.__start()
        self.cur.execute("""
        SELECT n FROM user 
        WHERE chat_id = ?;
        """, (message.chat.id,))
        n = self.cur.fetchone()[0]
        self.__close()
        return n

    def update_n(self, message, n):
        self.__start()
        self.cur.execute("""
           UPDATE user 
           SET n = ?
           WHERE chat_id = ?; 
           """, (n, message.chat.id))
        self.__close()

    def update_tasks(self, message, task, date=None, shop=False):
        self.__start()
        if not shop:
            if '✅' in task:
                self.cur.execute("""
                UPDATE task 
                SET content = ?
                WHERE content = ? AND date = ? AND chat_id = ?; 
                """, (task.strip('✅'), task, date, message.chat.id))
            else:
                self.cur.execute("""
                UPDATE task 
                SET content = ?
                WHERE content = ? AND date = ? AND chat_id = ?; 
                """, ('✅' + task, task, date, message.chat.id))
        else:
            if '✅' in task:
                self.cur.execute("""
                UPDATE shop 
                SET item_name = ?
                WHERE item_name = ? AND chat_id = ?; 
                """, (task.strip('✅'), task, message.chat.id))
            else:
                self.cur.execute("""
                UPDATE shop 
                SET item_name = ?
                WHERE item_name = ? AND chat_id = ?; 
                """, ('✅' + task, task, message.chat.id))
        self.__close()

    def delete_task(self, message, task):
        self.__start()
        if isinstance(task, str):
            self.cur.execute("""
            DELETE FROM task WHERE content = ? AND chat_id = ?;
            """, (task, message.chat.id))
        elif isinstance(task, (list, tuple)):
            for t in task:
                self.cur.execute("""
                DELETE FROM task WHERE content = ? AND chat_id = ?;
                """, (t, message.chat.id))
        self.__close()

    def delete_items(self, message, items=(), review=False):
        self.__start()
        if review:
            self.cur.execute("""
            DELETE FROM shop WHERE chat_id = ?;
            """, (message.chat.id,))
        else:
            for item in items:
                self.cur.execute("""
                DELETE FROM shop WHERE item_name = ? AND chat_id = ?;
                """, (item, message.chat.id))
        self.__close()



