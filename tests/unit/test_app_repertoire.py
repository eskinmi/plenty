import pytest
import mock

from app.db.repertoire import Repertoire


@pytest.fixture
def plantae_id():
    return '1'


@pytest.fixture
def repertoire():
    return [
        (
            '1',
            'macaroni',
            '{"indoor": true, "isolation": {"score": 0.5}, "light": {"score": 0.7}, "drainage": {"score": 0.5}}',
            'random_species'
         )
    ]


@mock.patch('app.db.care.CareHistory.get')
@mock.patch('app.db.care.CareNeeds.get')
@mock.patch('app.db.taxonomy.PlantTaxonomy.query')
@mock.patch('app.db.repertoire.Repertoire.query')
def test_repertoire(mock_query,
                    mock_taxonomy_query,
                    mock_needs,
                    mock_hist,
                    repertoire
                    ):
    mock_query.return_value = repertoire
    rep = Repertoire()
    assert rep.exists
    assert len(rep.L) == 1
    assert rep.L[0].id == '1'
    assert rep.dicts[0]['conditions']['isolation']['score'] == 0.5
