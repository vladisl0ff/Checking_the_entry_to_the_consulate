import sqlite3
from typing import Dict, Any, Tuple, Optional


class UserDatabase:
    """
    Class for working with the user database.
    """

    def __init__(self, db_name: str = 'user.db'):
        """
        Initialize the database when creating an instance of the class.

        :param db_name: The name of the database.
        """
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

    def create_table(self) -> None:
        """
        Create the users table if it doesn't exist yet.
        """
        create_table_query = '''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY UNIQUE NOT NULL,
                user_id INTEGER UNIQUE NOT NULL,
                url TEXT,
                time INTEGER NOT NULL,
                application_number TEXT,
                security_code TEXT
            )
        '''
        self.cursor.execute(create_table_query)
        self.conn.commit()

    def save_user_data(self, user_id: int, data: Dict[str, Any]) -> None:
        """
        Save user data to the database.

        :param user_id: The user's ID.
        :param data: A dictionary containing user data.
        """
        insert_query = "INSERT INTO users (user_id, url, time, application_number, security_code) VALUES (?, ?, ?, ?, ?)"
        values: Tuple[Any, ...] = (user_id, data['url'], data['time'], data['id_value'], data['cd_value'])
        self.cursor.execute(insert_query, values)
        self.conn.commit()

    def update_user_data(self, user_id: int, data: Dict[str, Any]) -> None:
        """
        Update user data in the database.

        :param user_id: The user's ID.
        :param data: A dictionary containing updated user data.
        """
        update_query = "UPDATE users SET url = ?, time = ?, application_number = ?, security_code = ? WHERE user_id = ?"
        values: Tuple[Any, ...] = (data['url'], data['time'], data['id_value'], data['cd_value'], user_id)
        self.cursor.execute(update_query, values)
        self.conn.commit()

    def get_user_data(self, user_id: int) -> Optional[Tuple[str, int]]:
        """
        Get user data by their ID.

        :param user_id: The user's ID.
        :return: A tuple containing the user's URL and time, or None if the user is not found.
        """
        select_query = "SELECT url, time FROM users WHERE user_id = ?"
        self.cursor.execute(select_query, (user_id,))
        return self.cursor.fetchone()

    def close(self) -> None:
        """
        Close the connection to the database.
        """
        self.conn.close()
