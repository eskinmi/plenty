import os
import logging
import time
from functools import wraps
from typing import List, Dict


logger = logging.getLogger('model utilities')


def read_image(path):
    """ Read image from the path in bytes """
    with open(path, 'rb') as image_file:
        image = image_file.read()
    return image


def _map_response_with_func(res: List[Dict], map_func=None):
    if map_func:
        return list(map(
            lambda x: map_func(x),
            res
        ))
    else:
        return res


def format_prediction_response(res: Dict,
                               response_type: str,
                               response_map_func=None,
                               **kwargs
                               ):
    """
    Format the response from prediction.

    Parameters
    ----------
    res: Dict
        prediction results
    response_type: str
        response type.
        {best, topn}
    response_map_func: func
        response mapping function
    **kwargs

    Returns
    -------
    List[Dict]
        mapped response
    """
    if not isinstance(res, dict):
        logger.error('response type should be a dict.')
        raise ValueError('response type should be a dict.')
    if response_type == 'best':
        r = res['results'][:1]
    elif response_type == 'topn':
        topn = kwargs.get('topn', 3)
        r = res['results'][:topn]
    else:
        logger.error('response type can be ranked or top.')
        raise ValueError('response type can be ranked or top.')
    return _map_response_with_func(r, response_map_func)


def with_images_check(func):
    @wraps(func)
    def apply_with_check(path, *args, **kwargs):
        if not os.listdir(path):
            logger.error('there are no images to detect.')
            return FileNotFoundError('there are no images to detect.')
        return func(path, *args, **kwargs)
    return apply_with_check


def gen_version_id():
    return str(round(time.time() * 1000))


def find_latest_model_version(model_path: str):
    if versions := os.listdir(model_path):
        logger.debug(F'found model versions : {versions}')
        return max(versions)
    else:
        logger.error('could not find any versions.')
        raise ValueError(
            """
            could not find any versions. please check the path.
            """
        )
