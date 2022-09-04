import pytest
import mock
from contextlib import ExitStack, contextmanager

from app.db.repertoire import PlantUnit
from app.db.repertoire import Repertoire
from app.db.repertoire import PlantIdNotKnownException


@contextmanager
def nested_ctx(*contexts):
    """
    Reimplementation of nested in python 3.
    """
    with ExitStack() as stack:
        for ctx in contexts:
            stack.enter_context(ctx)
        yield contexts


@pytest.fixture
def plantae_id():
    return 0


@pytest.fixture
def repertoire():
    return [
        {
            "id": 1,
            "name": "another-fake-plant",
            "conditions": {
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
        }
    ]


@pytest.fixture
def needs():
    return []


@mock.patch('os.path.exists', return_value=True)
@mock.patch('plenty.utils.read_json')
@mock.patch('app.db.care.History.get')
@mock.patch('app.db.care.CareNeeds.get')
def test_plant_unit_get_fail(mock_care_plant,
                             mock_history_load,
                             mock_read_json,
                             mock_os,
                             plantae_id,
                             repertoire
                             ):
    mock_read_json.return_value = repertoire
    with pytest.raises(PlantIdNotKnownException):
        p = PlantUnit()
        p.get(plantae_id)


@mock.patch('os.path.exists', return_value=True)
@mock.patch('plenty.utils.read_json')
@mock.patch('app.db.care.History.get')
@mock.patch('app.db.care.CareNeeds.get')
def test_repertoire(mock_care_plant,
                    mock_history_load,
                    mock_read_json,
                    mock_os,
                    repertoire
                    ):
    mock_read_json.return_value = repertoire
    rep = Repertoire()
    assert rep.exists
    assert len(rep.L) == 1
    assert rep.L[0].id == 1
