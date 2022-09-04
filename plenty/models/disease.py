import os
import logging
from typing import Tuple
import numpy as np
import tensorflow as tf

from plenty.models.utils import with_images_check
from plenty.models.utils import format_prediction_response
from plenty.models.utils import find_latest_model_version
from plenty.utils import read_json

""" Disease Detection Model and Utilities """


logger = logging.getLogger("app.models.disease")
TMP_IMAGES_PATH = './tmp/images/'


class DiseaseDetector:
    model_dir = './artifacts/disease/'
    version_id = None
    model = None
    indices = None
    params = None

    @classmethod
    def get(cls, version_id=None):
        if not cls.model:
            logger.debug('disease model data is not already loaded.')
            if os.path.exists(cls.model_dir):
                if version_id is None:
                    version_id = find_latest_model_version(cls.model_dir)
                    logger.debug(F'model version: {version_id}')
                model_path = os.path.join(cls.model_dir, cls.version_id)
                logger.debug(F'collecting model data.')
                cls.version_id = version_id
                cls.model = tf.keras.models.load_model(model_path + '/plant-disease.h5')
                cls.indices = read_json(model_path + '/indices.json')
                cls.params = read_json(model_path + '/params.json')
            else:
                logger.error(F'file not found: {cls.model_dir}')
                raise FileNotFoundError(cls.model_dir)


@with_images_check
def _get_images_input(images_path):
    """ Read images from path. """
    logger.info(F'collecting images from : {images_path}')
    return [
        tf.keras.preprocessing.image.load_img(os.path.join(images_path, img_key))
        for img_key in os.listdir(images_path)
    ]


def process_images(images, target_size: Tuple[int, int] = (256, 256)):
    """
    Process images. Read, resize, and rescale.
    Parameters
    ----------
    images: List[Img]
        array of images
    target_size: Tuple[int, int]
        target size to resize images.

    Returns
    -------
    List[np.array. ...]
        images arrays
    """
    logger.info('processing images.')
    images_processed = [
        image.resize(target_size).convert('RGB')
        for image in images
    ]
    images_arr = np.asarray([
        tf.keras.preprocessing.image.img_to_array(image_proc)
        for image_proc in images_processed
    ])
    images_arr = images_arr / 255
    return images_arr


def predict(response_type='ranked', **kwargs):
    """
    Perform disease detection.

    Parameters
    ----------
    response_type: str
        ['ranked', 'topn']
    kwargs

    Returns
    -------
    Dict
        prediction result dictionary.
    """
    detector = DiseaseDetector.get()
    images_path = kwargs.get('path', TMP_IMAGES_PATH)
    images = _get_images_input(images_path)
    images_arr = detector.process_images(images)
    predictions_raw = detector.model.predict(images_arr)
    predicted_class = [
        detector.indices[np.argmax(i)]
        for i in predictions_raw
    ]
    predicted_proba = [
        float(np.max(pred))
        for pred in predictions_raw
    ]
    r = {
        'results': [
            {
                'image_key': key,
                'prediction': predicted_class[ix],
                'proba': predicted_proba[ix]
            }
            for ix, key in enumerate(os.listdir(TMP_IMAGES_PATH))
        ]
    }
    logger.debug(F'disease prediction output : {r}')
    return format_prediction_response(
            r,
            response_type,
            **kwargs
    )
