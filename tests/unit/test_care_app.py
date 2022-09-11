import pytest
import mock
import datetime as dt

from app.db.care import CareHistory
from app.db.care import CareNeeds


@pytest.fixture
def plantae_id():
    return 'guacamole'


@pytest.fixture()
def hist():
    return [
        ('guacamole', 'water', '2022-05-24'),
        ('guacamole', 'water', '2022-05-29'),
        ('guacamole', 'shower', '2022-05-23'),
        ('guacamole', 'dust', '2022-05-27'),
        ('guacamole', 'feed', '2022-05-27'),
        ('guacamole', 'mist', '2022-05-23')
    ]


@pytest.fixture
def history(plantae_id, hist):
    with mock.patch.object(CareHistory, 'query', return_value=hist):
        yield CareHistory(plantae_id)


@pytest.fixture
def needs():
    return {
        "macaroni": {
            "water": {
                "freq": 0.15,
                "amount": 0.5,
                "watering_type": "top"
            }
        }
    }


def test_history_call(history):
    assert history('dust') == [dt.date(2022, 5, 27)]


def test_care_needs_get(needs):
    CareNeeds.data = needs
    n = CareNeeds.get('macaroni')
    assert n['water']['freq'] == 0.15
