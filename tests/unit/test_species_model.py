import pytest
from mock import patch

from plenty.models.species import predict


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
@patch('requests.post')
@patch('plenty.models.species.load_images')
def test_get_prediction_best_response(mock_image_loader, mock_request, mock_utils_get_api_key, success_response):
    mock_image_loader.return_value = [None], ['']
    mock_utils_get_api_key.return_value = apikey
    mock_request.return_value = success_response
    prediction = predict('best')
    assert prediction[0]['proba'] == 1.0
    assert len(prediction) == 1


@patch('plenty.api.util.get_api_key')
@patch('requests.post')
@patch('plenty.models.species.load_images')
def test_get_prediction_topn_response(mock_image_loader, mock_request, mock_utils_get_api_key, success_response):
    mock_image_loader.return_value = [None], ['']
    mock_utils_get_api_key.return_value = apikey
    mock_request.return_value = success_response
    prediction = predict('topn', n=3)
    assert len(prediction) == 2
