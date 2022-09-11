import mock
import pytest

from plenty.care import optimisers


@pytest.fixture
def needs():
    return {
        "water": {
            "freq": 0.15,
        },
        "light": {
            "score": 0.7,
            "direct": False
        },
        "air": {
            "temperature": {
                "min": 15,
                "max": 26
            }
        },
        "drainage": {
            "score": 0.5
        },
        "mist": {
            "freq": 0.05
        },
        "shower": {
            "freq": 0
        },
        "fertilize": {
            "type": "common",
            "freq": 0.01
        },
        "dust": {
            "freq": 0.01
        }
    }


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


@pytest.fixture
def external_cond():
    return {
        'tavg': []
    }


@mock.patch.object(optimisers.WaterOpt, 'set_temperature_weight')
@mock.patch.object(optimisers.WaterOpt, 'set_drainage_weight')
def test_water_opt(plant_cond,
                   external_cond,
                   needs
                   ):
    optimiser = optimisers.get('water')
    res = optimiser.opt(
        needs['water']['freq'],
        needs,
        plant_cond,
        external_cond

    )
    assert round(res, 2) == needs['water']['freq']


@mock.patch.object(optimisers.MistOpt, 'set_temperature_weight')
@mock.patch.object(optimisers.MistOpt, 'set_light_weight')
def test_mist_opt(plant_cond,
                  external_cond,
                  needs
                  ):
    optimiser = optimisers.get('mist')
    res = optimiser.opt(
        needs['mist']['freq'],
        needs,
        plant_cond,
        external_cond

    )
    assert round(res, 2) == needs['mist']['freq']
