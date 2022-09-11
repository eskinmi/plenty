import pytest
from mock import patch
import datetime as dt
import pandas as pd

from plenty.api.openweathermap import process_history_req_input
from plenty.api.openweathermap import geocoding_req
from plenty.api.openweathermap import history_req
from plenty.api.openweathermap import get_point


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data


@pytest.fixture
def geo_success_response_dict():
    return [{'lat': 10, 'lon': 10}]


@pytest.fixture
def hist_success_response_dict():
    return [pd.DataFrame([])]


@pytest.fixture
def apikey():
    return '00apikey'


@pytest.fixture
def geo_success_response(geo_success_response_dict):
    return MockResponse(
        geo_success_response_dict,
        200
    )


@pytest.fixture
def hist_success_response(hist_success_response_dict):
    return MockResponse(
        hist_success_response_dict,
        200
    )


@pytest.fixture
def lat():
    return 10.002736


@pytest.fixture
def lon():
    return 10.012310


@pytest.fixture
def start():
    return dt.datetime(2022, 7, 27, 0, 0, 0, 0, tzinfo=dt.timezone.utc)


@pytest.fixture
def days_back():
    return 5


def test_process_history_req_input(lat, lon, start, days_back):
    res = process_history_req_input(
        lat, lon, start, days_back
    )
    assert res[0] == 10.00
    assert res[1] == 10.01
    assert isinstance(res[2], float)
    assert isinstance(res[3], float)


@patch('plenty.api.util.get_api_key')
@patch('requests.get')
def test_geocoding_req(mock_request_get,
                       mock_utils_get_api_key,
                       apikey,
                       geo_success_response
                       ):
    mock_utils_get_api_key.return_value = apikey
    mock_request_get.return_value = geo_success_response
    res, success = geocoding_req('Utrecht', None, 'NL', 1)
    assert success
    assert res['lat'] == 10
    assert res['lon'] == 10


@patch('plenty.api.util.get_api_key')
@patch('requests.get')
def test_history_req(mock_request_get,
                     mock_utils_get_api_key,
                     hist_success_response,
                     lat,
                     lon,
                     start,
                     days_back
                     ):
    mock_utils_get_api_key.return_value = apikey
    mock_request_get.return_value = hist_success_response
    res, success = history_req(lat, lon, start, days_back)
    assert success
    assert res.empty


@patch('plenty.api.openweathermap.save_geocode_response')
@patch('plenty.api.openweathermap.read_json')
@patch('plenty.api.util.get_api_key')
@patch('requests.get')
def test_get_point_saved(mock_request_get,
                         mock_utils_get_api_key,
                         mock_read_json,
                         mock_save,
                         apikey,
                         geo_success_response,
                         lat,
                         lon
                         ):
    mock_read_json.return_value = {'Utrecht,NL': [10.2000, 10.3000]}
    mock_save.return_value = None
    mock_utils_get_api_key.return_value = apikey
    mock_request_get.return_value = geo_success_response
    lat, lon = get_point('Utrecht', None, 'NL')
    assert lat == 10.2000 and lon == 10.3000


@patch('plenty.api.openweathermap.save_geocode_response')
@patch('plenty.api.openweathermap.read_json')
@patch('plenty.api.util.get_api_key')
@patch('requests.get')
def test_get_point_unsaved(mock_request_get,
                           mock_utils_get_api_key,
                           mock_read_json,
                           mock_save,
                           apikey,
                           geo_success_response,
                           lat,
                           lon
                           ):
    mock_read_json.return_value = {}
    mock_save.return_value = None
    mock_utils_get_api_key.return_value = apikey
    mock_request_get.return_value = geo_success_response
    lat, lon = get_point('Utrecht', None, 'NL')
    assert lat == 10.0 and lon == 10.0
