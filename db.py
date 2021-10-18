from datastructures import PunishedUser

import time
from typing import Union, List
from pathlib import Path
import logging

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
        statement = "CREATE TABLE IF NOT EXISTS wen_timeouts (member_id INTEGER PRIMARY KEY, guild_id INTEGER, counter INTEGER, currently_banned INTEGER, last_ban INTEGER);"

        try:
            cursor = self.connection.cursor()
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

    def get_timeout(self, member_id: int, guild_id: int) -> Union[None, int]:
        query = f"SELECT counter FROM wen_timeouts WHERE member_id = {member_id} AND guild_id = {guild_id};"
        result = self.query(query, False)
        if result is not None and len(result) > 0:
            return result[0]
        return

    def update_timeout(self, member_id: int, guild_id: int, updated_timeout: int):
        statement = f"UPDATE wen_timeouts SET counter = {updated_timeout}, last_ban = {int(time.time())}, currently_banned = 1 WHERE member_id = {member_id} AND guild_id = {guild_id};"
        self.execute(statement)

    def create_timeout_entry(self, member_id: int, guild_id: int):
        statement = f"INSERT INTO wen_timeouts VALUES ({member_id}, {guild_id}, 1, 1, {int(time.time())});"
        self.execute(statement)

    def set_unbanned(self, member_id: int, guild_id: int):
        statement = f"UPDATE wen_timeouts SET currently_banned = 0 WHERE member_id = {member_id} AND guild_id = {guild_id};"
        self.execute(statement)

    def remove_entry(self, member_id: int, guild_id: int):
        statement = f"DELETE FROM wen_timeouts WHERE member_id = {member_id} AND guild_id = {guild_id};"
        self.execute(statement)

    def get_currently_punished_users(self, permaban_threshold: int) -> Union[None, List[PunishedUser]]:
        query = f"SELECT member_id, counter, last_ban FROM wen_timeouts WHERE currently_banned = 1 AND counter <= {permaban_threshold};"
        results = self.query(query, True)
        if results is not None and len(results) > 0:
            return [PunishedUser(result[0], result[1], result[2]) for result in results]
        return
