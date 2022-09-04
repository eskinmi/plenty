import os


def get_api_key(name: str = 'plantnet'):
    api_path = F'./{name}_apikey.txt'
    if os.path.exists(api_path):
        with open(F'./{name}_apikey.txt') as f:
            key = f.read()
    else:
        raise ValueError(
            """
            couldn't find any api key document named: {file_name}.
            please insert api key document to top directory.
            """.format(file_name=api_path)
        )
    return key
