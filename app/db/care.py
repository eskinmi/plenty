import json
import datetime as dt
import logging
from typing import Union

from app.db import PlentyDatabase


logger = logging.getLogger('app.care.care')


class CareHistory:
    _schema = [
        "id text, cond text, date text"
    ]

    def __init__(self, plantae_id: str):
        self.plantae_id = plantae_id
        self.hist = self.get(self.plantae_id)
        self.today = dt.date.today()

    @staticmethod
    def query(plantae_id):
        with PlentyDatabase() as db:
            q = db.cursor.execute(
                "SELECT * FROM care_history WHERE id = :plant_id",
                {'plant_id': plantae_id}
            )
            res = q.fetchall()
        return res

    def get(self, plantae_id):
        if q := self.query(plantae_id):
            return q
        else:
            logger.debug(
                """
                no history found for plant: {plantae_id}
                """.format(plantae_id=plantae_id)
            )
            return []

    def add(self, date: Union[str, dt.date], cond: str):
        with PlentyDatabase() as db:
            db.insert(table='care_history', values=(self.plantae_id, cond, date))

    def __call__(self, key):
        return [
            dt.datetime.strptime(row[2], "%Y-%m-%d").date()
            for row in self.hist
            if row[1] == key
        ]


class CareNeeds:
    _schema = [
        'name text, opt_cond_map text'
    ]
    data = dict()

    @staticmethod
    def query(name):
        with PlentyDatabase() as db:
            q = db.cursor.execute(
                "SELECT * FROM care_needs WHERE name = :name",
                {'name': name}
            )
            res = q.fetchone()
        return res

    @classmethod
    def get(cls, plantae_name: str):
        if not cls.data.get(plantae_name):
            needs = cls.query(plantae_name)
            res = json.loads(needs[1])
            cls.data[plantae_name] = res
            return res
        else:
            logger.debug('data is already loaded.')
            return cls.data.get(plantae_name, {})