import logging
from typing import Union
import requests
import datetime as dt

from plenty.api import util
from plenty.utils import write_json, read_json

""" OPENWEATHER API UTILS """

# logging.basicConfig(filename='./app_logs.txt', level=logging.DEBUG)
logger = logging.getLogger('app.api.openweathermap')


# GET API ENDPOINTS
GEOCODES_SAVE_PATH = './store/geocodes.json'
HISTORY_API_ENDPOINT_RAW = 'https://history.openweathermap.org/data/2.5/history/city?' \
                           'lat={lat}&lon={lon}&type=hour&start={start}&end={end}&units=metric&appid={api_key}'
GEOCODE_API_ENDPOINT_RAW = 'http://api.openweathermap.org/geo/1.0/direct?q=' \
                           '{loc}&limit={limit}&appid={api_key}'


def _get_history_endpoint(latitude, longitude, start, end):
    return HISTORY_API_ENDPOINT_RAW.format(
        lat=latitude,
        lon=longitude,
        start=start,
        end=end,
        api_key=util.get_api_key('openweathermap')
    )


def _get_geocode_endpoint(location, limit):
    return GEOCODE_API_ENDPOINT_RAW.format(
        loc=location,
        api_key=util.get_api_key('openweathermap'),
        limit=limit
    )


def _timestamp_to_ms(t):
    return t.replace(tzinfo=dt.timezone.utc).timestamp()


def _merge_loc_params(city, state_code, country_code):
    return ','.join([i for i in [city, state_code, country_code] if i])


def process_history_req_input(lat: Union[int, float],
                              lon: Union[int, float],
                              start: dt.time = None,
                              days_back: int = 7
                              ):
    if start is None:
        start = dt.datetime.now(dt.timezone.utc)
    return (
        round(lat, 2),
        round(lon, 2),
        _timestamp_to_ms(start),
        _timestamp_to_ms(start - dt.timedelta(days=days_back))
    )


def save_geocode_response(res, loc):
    logger.info('reading existing geocode data.')
    d = read_json(GEOCODES_SAVE_PATH)
    if loc not in d.keys():
        d.update(
            {loc: [res['lat'], res['lon']]}
        )
    logger.info('saving geocode response.')
    write_json(
        GEOCODES_SAVE_PATH,
        d
    )


def geocoding_req(city: str,
                  state_code: str = None,
                  country_code: str = None,
                  limit: int = 1
                  ):
    LOC = _merge_loc_params(city, state_code, country_code)
    print(F'loc : {LOC}')
    url = _get_geocode_endpoint(LOC, limit)
    print(F'url: {url}')
    try:
        res = requests.get(url)
        print(F'res: {res}')
        if res.status_code == 200:
            logger.info('geocode api fetch so good!')
            return res.json().pop(), True
        else:
            logger.warning(
                """
                geocode api request failed with
                status: {status}
                message: {message}
                """.format(
                    status=res.status_code,
                    message=res.text
                )
            )
            return {}, False
    except requests.exceptions.RequestException as e:
        logger.exception(e)
        return str(e), False


def history_req(lat: Union[int, float],
                lon: Union[int, float],
                start: dt.time = None,
                days_back: int = 7
                ):
    lat, lon, start, end = process_history_req_input(
        lat, lon, start, days_back
    )
    url = _get_history_endpoint(lat, lon, start, end)
    try:
        res = requests.get(url)
        print(F'res: {res}')
        if res.status_code == 200:
            logger.info('openweather api fetch so good!')
            return res.json().pop(), True
        else:
            logger.warning(
                """
                openweather api request failed with
                status: {status}
                message: {message}
                """.format(
                    status=res.status_code,
                    message=res.text
                )
            )
            return {}, False
    except requests.exceptions.RequestException as e:
        logger.exception(e)
        return str(e), False


def get_point(city: str,
              state_code: str = None,
              country_code: str = None
              ):
    LOC = _merge_loc_params(city, state_code, country_code)
    if saved_loc := read_json(GEOCODES_SAVE_PATH).get(LOC):
        logger.info(f'{LOC} is in existing geocode data.')
        lat, lon = saved_loc
    else:
        logger.info(f'{LOC} is not in existing geocode data.')
        gr, success = geocoding_req(city, state_code, country_code)
        if success:
            save_geocode_response(gr, LOC)
        lat, lon = gr.get('lat', None), gr.get('lon', None)
    return lat, lon


def get_history(city: str,
                state_code: str = None,
                country_code: str = None,
                start: dt.time = None,
                days_back: int = 7
                ):
    logging.info('getting weather history.')
    lat, lon = get_point(city, state_code, country_code)
    hr, _ = history_req(
        lat,
        lon,
        start,
        days_back
    )
    return hr
