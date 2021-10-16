from typing import Union

import logging
import time
from pathlib import Path

import sqlite3
from sqlite3 import Error

logging.basicConfig(format="%(name)s - %(levelname)s - %(message)s")


class Database:
    def __init__(self, database):
        self.connection = self.create_db_connection(database)
        self.create_table()

    @staticmethod
    def create_db_connection(db_file: Path):
        """Creates a connection to a specified SQLite database file

        :param db_file: Path to the SQLite database file
        :return:
        """
        conn = None
        try:
            conn = sqlite3.connect(db_file)
            return conn
        except Error as e:
            logging.warning(e)

        return conn

    def create_table(self):
        """Creates wen_timeouts table in case it doesn't already exist

        :return:
        """
        statement = "CREATE TABLE IF NOT EXISTS wen_timeouts (member_id INTEGER PRIMARY KEY, counter INTEGER, last_ban INTEGER);"

        try:
            cursor = self.connection()
            cursor.execute(statement)
            self.connection.commit()
        except Error as e:
            logging.error(e)

    def execute(self, statement: str):
        try:
            cursor = self.connection.cursor()
            cursor.execute(statement)
            self.connection.commit()
        except Error as e:
            logging.error(e)

    def query(self, query: str, fetchall: bool):
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)

            if fetchall:
                return cursor.fetchall()
            return cursor.fetchone()

        except Error as e:
            logging.error(e)
            return

    def get_timeout(self, member_id: int) -> Union[None, int]:
        query = f"SELECT member_id, counter, last_ban FROM wen_timeouts WHERE member_id = {member_id};"
        result = self.query(query, False)
        if len(result) > 0:
            return result[0]
        return

    def update_timeout(self, member_id: int, count: int):
        statement = f"UPDATE wen_timeouts SET count = {count + 1}, time = {int(time.time())} WHERE member_id = {member_id};"
        self.execute(statement)

    def create_timeout_entry(self, member_id: int):
        statement = f"INSERT INTO wen_timeouts VALUES ({member_id}, {1}, {int(time.time())});"
        self.execute(statement)

    def remove_entry(self, member_id: int):
        statement = f"DELETE FROM wen_timeouts WHERE member_id = {member_id}"
        self.execute(statement)
