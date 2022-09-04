import logging
import requests
from typing import List
import random

from plenty.api import util

logger = logging.getLogger('app.api.plantnet')


def get_endpoint():
    try:
        return F"https://my-api.plantnet.org/v2/identify/all?api-key={util.get_api_key('plantnet')}"
    except FileNotFoundError as e:
        logger.error(str(e))
        raise e


def _gen_rand_image_path(image_path):
    logger.info('generating random image paths.')
    if not image_path:
        return F'path_{round(random.random(), 4)}'
    else:
        return image_path


def get_prediction(images: List,
                   organs: List[str],
                   image_paths=None
                   ):
    data = {'organs': organs}
    path_given = True
    if image_paths is None:
        path_given = False
        image_paths = [None] * len(images)
    image_files = [
        (
            'images',
            (_gen_rand_image_path(path) if not path_given else image_paths[ix], img)
        )
        for ix, (img, path) in enumerate(zip(images, image_paths))
    ]
    try:
        logger.info('requesting image prediction from plantnet.')
        api_url = get_endpoint()
        res = requests.post(api_url, files=image_files, data=data)
        logger.debug(F'request status code: {res.status_code}')
        if res.status_code == 200:
            return res.json(), True
        else:
            return {}, False
    except requests.exceptions.RequestException as e:
        logger.exception(F'request exception: {str(e)}')
        return str(e), False
