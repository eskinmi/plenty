from app.db import PlentyDatabase

# TODO : create taxonomy database
# TODO : add taxonomy data.


class Taxonomy:
    columns = [
        'phylum',
        'class',
        'order',
        'family',
        'genus',
        'species'
    ]
    _schema = ','.join([
        F'{c} text'
        for c in columns
    ])

    def __init__(self, species: str = None):
        self.species = species
        for c in self.columns:
            self.__setattr__(c, None)
        self.get(self.species)

    def query(self, species):
        with PlentyDatabase() as db:
            req = db.cursor.execute(
                " SELECT :columns FROM taxonomy WHERE species = :species",
                {
                    'species': species,
                    'columns': ','.join(self.columns)
                 }
            )
            res = req.fetchone()
        return res

    def get(self, species):
        if self.species:
            self.__dict__.update(
                {self.columns[i]: q[i] for i, q in enumerate(self.query(species))}
            )
