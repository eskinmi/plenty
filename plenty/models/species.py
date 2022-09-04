import os
from typing import List, Dict
import logging

from plenty.api.plantnet import get_prediction
from plenty.models.utils import with_images_check
from plenty.models.utils import read_image
from plenty.models.utils import format_prediction_response


# uploaded images path
IMAGES_PATH = './tmp/images/'

logger = logging.getLogger('app.models.species')


class PredictionFailureException(Exception):
    def __init__(self, message=None):
        if message is None:
            self.message = 'Failed Prediction'
        else:
            self.message = message
        super().__init__(self.message)


@with_images_check
def load_images(path):
    logger.info('loading images from path.')
    images = []
    image_paths = []
    for key in os.listdir(path):
        image_path = os.path.join(path, key)
        image = read_image(image_path)
        images.append(image)
        image_paths.append(image_path)
    return image_paths, images


def _parse_response_results(r: Dict):
    logger.info('parsing prediction results.')
    return {
        'proba': r['score'],
        'scientificName': r['species'].get('scientificNameWithoutAuthor', str()),
        'commonNames': r['species'].get('commonNames', [])[:1],
    }


def predict(response_type='best', **kwargs):
    logger.info('inside species prediction method.')
    path = kwargs.get('path', None)
    if path is None:
        logger.debug('path is not given.')
        path = IMAGES_PATH
    image_paths, images = load_images(path)
    organs = ['leaf'] * len(images)
    res, success = get_prediction(images, organs, image_paths)
    if success:
        return format_prediction_response(
            res,
            response_type,
            response_map_func=_parse_response_results,
            **kwargs
        )
    else:
        logger.error(F'prediction failed: {res}')
        raise PredictionFailureException(res)
