from typing import Tuple, List
from abc import ABC, abstractmethod

import sqlite3


class PlentyDatabase:

    def __init__(self):
        self.conn = sqlite3.connect('./store/plenty.db')
        self.cursor = self.conn.cursor()
        self.tables = self._get_tables()

    def _get_tables(self):
        self.cursor.execute('SELECT name from sqlite_master where type = "table"')
        return self.cursor.fetchall()

    def create_table(self, name, schema):
        self.cursor.execute(
            """
            CREATE TABLE {name}
            {schema}
            """.format(
                name=name,
                schema=schema
            )
        )

    def insert(self, table: str, values: Tuple):
        self.cursor.execute(
            " ".join(
                ["INSERT INTO", table, "VALUES", '(', ','.join(['?' for _ in values]), ')']
            ),
            values
        )

    def remove(self, table: str, conditions: List[str]):
        self.cursor.execute(
            " ".join(
                ["DELETE FROM", table, "WHERE", " AND ".join(conditions)]
            )
        )

    def __enter__(self):
        return self

    def __exit__(self, ext_type, exc_value, traceback):
        self.cursor.close()
        if isinstance(exc_value, Exception):
            self.conn.rollback()
        else:
            self.conn.commit()
        self.conn.close()


class PlentyBaseAppModel(ABC):
    """
    Base application for Plenty DB Models.
    The applications should have the following
        two methods:
            query: to query the database with a given value.
            get: to retrieve the values in the model instance.
    """

    @staticmethod
    @abstractmethod
    def query(**kwargs):
        pass

    @abstractmethod
    def get(self, **kwargs):
        pass
