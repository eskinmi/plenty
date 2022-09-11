import pytest
from mock import patch

from plenty.api.plantnet import get_endpoint
from plenty.api.plantnet import get_prediction


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data


@pytest.fixture
def success_response_dict():
    return {
            'results': [
                {
                    'score': 1.0,
                    'species': {
                        'scientificNameWithoutAuthor': 'Garbage Goober Plant',
                        'commonNames': ['Garbage Goober']
                    },
                },
                {
                    'score': 0.4,
                    'species': {
                        'scientificNameWithoutAuthor': 'Mr. Meekseeks Plant',
                        'commonNames': ['Mr. Meekseeks']
                    },
                },
            ]
        }


@pytest.fixture
def apikey():
    return '00apikey'


@pytest.fixture
def failed_response():
    return MockResponse(
        {'error': 'failed'},
        400
    )


@pytest.fixture
def success_response(success_response_dict):
    return MockResponse(
        success_response_dict,
        200
    )


@patch('plenty.api.util.get_api_key')
def test_get_api_endpoint(mock_utils_get_api_key, apikey):
    mock_utils_get_api_key.return_value = apikey
    endpoint = get_endpoint()
    assert endpoint == F"https://my-api.plantnet.org/v2/identify/all?api-key={apikey}"


@patch('plenty.api.util.get_api_key')
@patch('requests.post')
def test_get_prediction(mock_request, mock_utils_get_api_key, success_response):
    mock_utils_get_api_key.return_value = apikey
    mock_request.return_value = success_response
    r, success = get_prediction([None], ['leaf'], [None])
    assert success
    assert r['results'][0]['score'] == 1


@patch('plenty.api.util.get_api_key', return_value='invalid-value')
@patch('requests.post')
def test_get_prediction(mock_request, mock_utils_get_api_key, failed_response):
    mock_request.return_value = failed_response
    r, success = get_prediction([None], ['leaf'], [None])
    assert not success
    assert r == dict()
