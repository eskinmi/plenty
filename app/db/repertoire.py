import uuid
import json
from typing import List
import logging
from dataclasses import dataclass

from app.db import PlentyDatabase
from app.db.care import CareHistory
from app.db.care import CareNeeds
from app.db.taxonomy import Taxonomy


logger = logging.getLogger('app.repertoire')


class PlantIdNotKnownException(Exception):
    def __init__(self, plantae_id):
        self.plantae_id = plantae_id
        message = 'no matching plant id found in repertoire.'
        super().__init__(message)


@dataclass
class Plantae:
    name: str = None

    def __post_init__(self):
        if self.name:
            self.needs = CareNeeds.get(plantae_name=self.name)


class PlantUnit(Plantae):

    def __init__(self,
                 plantae_id: str = None,
                 name: str = None,
                 conditions: str = None
                 ):
        super(PlantUnit, self).__init__(name)
        self.id = plantae_id
        if conditions is None:
            self.conditions = dict()
        else:
            self.conditions = conditions
        self.hist = CareHistory(self.id)
        self.taxonomy = Taxonomy(None)  # not yet implemented

    @staticmethod
    def query(plantae_id):
        with PlentyDatabase() as db:
            q = db.cursor.execute(
                "SELECT * FROM repertoire WHERE id = :plantae_id", {'plantae_id': plantae_id}
            )
            res = q.fetchone()
        return res

    @classmethod
    def get(cls, plantae_id: str):
        q = cls.query(plantae_id)
        if q:
            PlantUnit(
                plantae_id=plantae_id,
                name=q[1],
                conditions=json.loads(q[2])
            )
        else:
            logger.error(
                """
                no matching plant id found in repertoire.
                """
            )

    def add_to_repertoire(self):
        with PlentyDatabase() as db:
            db.insert(
                'repertoire',
                (self.id, self.name, json.dumps(self.conditions))
            )

    def remove_from_repertoire(self):
        with PlentyDatabase() as db:
            db.remove('repertoire',
                      conditions=[F'id = {self.id}']
                      )


class Repertoire:
    _schema = [
        "id text, name text, cond text"
    ]

    def __init__(self):
        self.L = self.get()
        self.exists = any(self.L)

    @staticmethod
    def query():
        with PlentyDatabase() as db:
            q = db.cursor.execute("SELECT * FROM repertoire")
            res = q.fetchall()
        return res

    @classmethod
    def get(cls):
        return [
            PlantUnit(plantae_id=row[0],
                      name=row[1],
                      conditions=json.loads(row[2])
                      )
            for row in cls.query()
        ]

    @property
    def dicts(self):
        if self.L is not None:
            return [
                {
                    'id': p.id,
                    'name': p.name,
                    'conditions': p.conditions
                }
                for p in self.L
            ]
        else:
            return {}

    def add(self, name, conditions):
        p = PlantUnit(
            plantae_id=uuid.uuid4().hex,
            name=name,
            conditions=conditions
        )

        self.L.append(p)
        # update db
        p.add_to_repertoire()

    def remove(self, plantae_id: List[str]):
        p = [p for p in self.L if p.id == plantae_id]
        if not p:
            raise ValueError('plant with id not found!')
        self.L = [p for p in self.L if p.id not in p.id]
        # update db
        p.remove_from_repertoire()
