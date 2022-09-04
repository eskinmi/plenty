import mock
import pytest
import datetime as dt

from app.db.repertoire import PlantUnit
from plenty.care import planners
from plenty.care.planners import dates_to_binary
from plenty.care import History
from plenty.care import CareNeeds
# from plenty.climate import ClimateConditions


@pytest.fixture
def run_date():
    return dt.date(2022, 5, 30)


@pytest.fixture
def plantae_id():
    return 0


@pytest.fixture
def plant_name():
    return 'im-am-so-fake'


@pytest.fixture
def plant_cond():
    return {
        "indoor": True,
        "isolation": {
            "score": 0.5
        },
        "light": {
            "score": 0.7
        },
        "drainage": {
            "score": 0.5
        }
    }


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
def needs():
    return {
        "im-am-so-fake": {
            "water": {
                "freq": 0.20,
                "amount": 0.5,
                "watering_type": "top"
            }
        }
    }


@pytest.fixture
def plant(plantae_id, plant_name, plant_cond, hist):
    with mock.patch.object(History, '_load', return_value=hist):
        yield PlantUnit(plantae_id,
                        plant_name,
                        plant_cond
                        )


def test_dates_to_binary(plant, run_date, needs):
    CareNeeds.data = needs
    h = dates_to_binary(
            plant.hist('water'),
            from_date=run_date - dt.timedelta(10),
            to_date=run_date
    )
    assert any(h)
    assert sum(h) == 2
    assert h == [0, 0, 0, 0, 1, 0, 0, 0, 0, 1]


def test_naive_planner_step(plant, run_date, needs):
    CareNeeds.data = needs
    planner = planners.get_planner('naive')
    planner.lookback = 20
    binary_response = planner.step(
        plant,
        'water',
        run_date,
        optimise=False,
        impute=False
    )
    assert binary_response == 1


def test_dynamic_planner_step(plant, run_date, needs):
    CareNeeds.data = needs
    planner = planners.get_planner('dynamic')
    binary_response = planner.step(
        plant,
        'water',
        run_date,
        optimise=False,
        impute=False
    )
    assert binary_response == 0
