import logging

from app.db import PlentyDatabase

logger = logging.getLogger('app.taxonomy')


class PlantTaxonomy:
    columns = [
        'taxon_id',
        'scientific_name',
        'scientific_name_authorship',
        'taxon_rank',
        'family',
        'subfamily',
        'tribe',
        'subtribe',
        'genus',
        'subgenus',
        'specific_epithet'
    ]
    _schema = 'index number, ' + ','.join([
        F'{c} text'
        for c in columns
    ])

    def __init__(self, scientific_name: str = None, taxon_rank: str = 'species'):
        self.taxon_rank = taxon_rank
        self._name = scientific_name
        if self._name is not None:
            self.scientific_name = self._name.lower()
        else:
            self.scientific_name = None
        self.index = None
        self.query_response = None
        self.scientific_name_authorship = None
        self.family = None
        self.subfamily = None
        self.tribe = None
        self.subtribe = None
        self.genus = None
        self.subgenus = None
        self.specific_epithet = None
        self.get()

    @staticmethod
    def query(scientific_name, taxon_rank: str = 'species'):
        with PlentyDatabase() as db:
            req = db.cursor.execute(
                " SELECT * FROM taxonomy WHERE taxon_rank = :taxon_rank AND scientific_name = :scientific_name",
                {
                    'scientific_name': scientific_name,
                    'taxon_rank': taxon_rank
                 }
            )
            res = req.fetchone()
        return res

    def get(self):
        if self.scientific_name:
            self.query_response = self.query(self.scientific_name, self.taxon_rank.lower())
        if q := self.query_response:
            self.index = q[0]
            self.scientific_name_authorship = q[3]
            self.taxon_rank = q[4]
            self.family = q[5]
            self.subfamily = q[6]
            self.tribe = q[7]
            self.subtribe = q[8]
            self.genus = q[9]
            self.subgenus = q[10]
            self.specific_epithet = q[11]
        else:
            logger.error(F'taxonomy data cannot be found for: {self.scientific_name}')
