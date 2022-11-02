import logging

from app.db.base import PlentyBaseAppModel
from app.db import PlentyDatabase
from plenty.utils import read_img_binary
from typing import BinaryIO

logger = logging.getLogger('app.images')

STANDARD_IMAGE_DIMENSIONS = ('256', '256')


def process_image():
    raise NotImplemented


class Images(PlentyBaseAppModel):
    columns = [
        'plant_id',
        'image'
    ]
    _schema = 'plant_id text, image blob'

    def __init__(self, plant_id: str, image_path: str = None, image: BinaryIO = None):
        self.plant_id = plant_id
        if image_path is not None:
            self.image = read_img_binary(image_path)
        elif image is not None:
            self.image = image
        else:
            if q := self.query(self.plant_id):
                self.image = q[1]
            else:
                self.image = None
        # TODO: add image resizing / processing

    @staticmethod
    def query(plant_id):
        with PlentyDatabase() as db:
            req = db.cursor.execute(
                "SELECT * FROM images WHERE plant_id = :plant_id",
                {
                    'plant_id': plant_id,
                 }
            )
            res = req.fetchone()
        return res

    @staticmethod
    def query_any(plant_id):
        with PlentyDatabase() as db:
            req = db.cursor.execute(
                "SELECT * FROM images WHERE plant_id = :plant_id",
                {
                    'plant_id': plant_id,
                }
            )
            res = req.fetchall()
        return res

    @classmethod
    def get(cls, plant_id):
        q = cls.query(plant_id)
        if q:
            return Images(plant_id, q[1])
        else:
            logger.error('Image could not be found for plant id.')

    @staticmethod
    def add(plant_id: str, image: BinaryIO):
        with PlentyDatabase() as db:
            db.insert(table='images', values=(plant_id, image))
