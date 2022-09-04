import pytest
import mock
import datetime as dt

from plenty.care import History
from plenty.care import CareNeeds


@pytest.fixture
def plantae_id():
    return 0


@pytest.fixture()
def hist():
    return {
            "water": ["2022-05-24", "2022-05-29"],
            "shower": ["2022-05-23"],
            "dust": ["2022-05-27"],
            "feed": ["2022-05-27"],
            "mist": ["2022-05-23"]
        }


@pytest.fixture
def history(plantae_id, hist):
    with mock.patch.object(History, '_load', return_value=hist):
        yield History(plantae_id)


@pytest.fixture
def needs():
    return {
        "fake-plant": {
            "water": {
                "freq": 0.15,
                "amount": 0.5,
                "watering_type": "top"
            }
        }
    }


def test_history_add(history):
    history.add('2022-05-24', 'water')
    assert history.hist('water') == ["2022-05-24", "2022-05-29"]
    history.add('2022-06-25', 'water')
    assert '2022-06-25' in history.hist('water')


def test_history_call(history):
    assert history('dust') == [dt.date(2022, 5, 27)]


def test_care_needs_get(needs):
    CareNeeds.data = needs
    n = CareNeeds.get('fake-plant')
    assert n['water']['freq'] == 0.15
