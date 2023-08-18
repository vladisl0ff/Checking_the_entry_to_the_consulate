import sqlite3


class UserDatabase:
    def __init__(self, db_name='user.db'):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY UNIQUE NOT NULL,
                user_id INTEGER UNIQUE NOT NULL,
                url TEXT,
                time INTEGER NOT NULL,
                application_number STRING,
                security_code STRING
            )
        ''')
        self.conn.commit()

    def save_user_data(self, user_id, data):
        self.cursor.execute("INSERT INTO users (user_id, url, time, application_number, security_code) VALUES (?, ?, ?, ?, ?)", (user_id, data['url'], data['time'], data['id_value'], data['cd_value']))
        self.conn.commit()

    def update_user_data(self, user_id, data):
        self.cursor.execute("UPDATE users SET url = ?, time = ?, application_number = ?, security_code = ? WHERE user_id = ?", (data['url'], data['time'], data['id_value'], data['cd_value'], user_id))
        self.conn.commit()

    def get_user_data(self, user_id):
        self.cursor.execute("SELECT url, time FROM users WHERE user_id = ?", (user_id,))
        return self.cursor.fetchone()

    def close(self):
        self.conn.close()
