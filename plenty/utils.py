import os
import json
import logging


logger = logging.getLogger('app.utils')


def read_json(path):
    if os.path.exists(path):
        f = open(path, 'r')
        cond = json.load(f)
        f.close()
    else:
        logger.error(F'file not found: {path}')
        raise FileNotFoundError(path)
    return cond


def write_json(path, obj):
    with open(path, 'w') as f:
        json.dump(obj, f)


def get_user_info(path: str = './store/user.json'):
    return read_json(path)
