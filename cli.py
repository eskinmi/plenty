import pytest
import click
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from logging import StreamHandler


def _init_logger():
    log = logging.getLogger('app')
    log.setLevel(logging.DEBUG)
    fh = RotatingFileHandler('./logs.txt')
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    log.addHandler(fh)
    return log


def notify(title, text):
    os.system(
        """
        osascript -e 'display notification "{}" with title "{}"'
        """.format(text, title)
    )


def _plan_notification(plant, care_type, res):
    logger.info('running plan notifications')
    return str(
        """
        Next care times: 
            {days} 
        Plant info:
            name: {name}
            plant id: {plant_id}
        """.format(
            care_type=care_type,
            name=plant.name,
            plant_id=plant.id,
            days=','.join([str(res[0][ix]) for ix, v in enumerate(res[1]) if v == 1])
        )
    )


def _species_detection_notification(specie, common_name, proba):
    logger.info('running species detection notification')
    return str(
        """
        species are detected from images:
        specie: {specie}
        common_name: {common_name}
        probability: {proba} 
        """.format(
            specie=specie,
            common_name=common_name,
            proba=proba
        )
    )


@click.group()
@click.option('--debug/--no-debug', default=False)
@click.pass_context
def cli(ctx, debug):
    click.echo('Debug mode is %s' % ('on' if debug else 'off'))
    click.echo('Notification mode is %s' % ('on' if notify else 'off'))
    ctx.ensure_object(dict)
    ctx.obj['DEBUG'] = debug
    if debug:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        sh = StreamHandler(sys.stdout)
        sh.setLevel(logging.DEBUG)
        sh.setFormatter(formatter)
        logger.addHandler(sh)


@cli.command()
@click.pass_context
def run_tests(ctx):
    if ctx.obj['DEBUG']:
        click.echo("running tests on debug mode!")
    pytest.main(["tests"])


@cli.command()
@click.option("--care_type", default='water')
@click.option("--planner_type", default='dynamic', type=click.Choice(['dynamic', 'naive', 'bayes']))
@click.option("--impute", default=False)
@click.option("--n_days", default=7)
@click.pass_context
def plan(ctx, care_type, planner_type, impute, n_days):
    from app.db.repertoire import Repertoire
    from plenty.care import planners

    planner = planners.get_planner(planner_type)
    rep = Repertoire()
    for plant in rep.L:
        if ctx.obj['DEBUG']:
            click.echo('optimizing for %s' % plant.name)
        res = planner.plan(plant, care_type, optimise=True, impute=impute, n_days=n_days)
        if res:
            m = _plan_notification(plant, care_type, res)
            notify(f'Plenty Planner', m)


@cli.command()
@click.pass_context
def add_to_repertoire(ctx):

    from app.db.taxonomy import PlantTaxonomy
    from app.db.repertoire import Repertoire

    click.echo('Adding plant to the repertoire.')
    click.echo('Plant Identification Information: ')
    name = click.prompt(
        'plant name',
        type=str
    )

    while True:
        species = click.prompt(
            'plant species',
            type=str,
            value_proc=lambda x: x.lower()
        )
        if PlantTaxonomy.query(species):
            break
        else:
            click.echo('Species not found. Please provide the correct name.')
            # PlantTaxonomy.advanced_search(species)

    click.echo('Plant conditions information')
    click.echo('Please enter the scores between 0 and 1.')
    conditions = {
        'indoor': click.prompt('is this an indoor plant', default=True, type=bool, show_default=True),
        'isolation': {
            'score': click.prompt('score: how well is the room of the plant isolated',
                                  type=float,
                                  default=0.5,
                                  show_default=True
                                  )
        },
        'light': {
            'score': click.prompt('score: how much light the plant receives',
                                  type=float,
                                  default=0.5,
                                  show_default=True
                                  )
        },
        'drainage': {
            'score': click.prompt('score: how good is the drainage in the pot',
                                  type=float,
                                  default=0.5,
                                  show_default=True
                                  )
        }
    }

    click.echo('Adding plant to repertoire')
    rep = Repertoire()
    rep.add(name, conditions, species)
    click.echo('Success!')

    cont = click.prompt('Would you like to add more plants?',
                        default='n',
                        show_choices=True,
                        type=click.Choice(['y', 'n'])
                        )
    if cont == 'y':
        ctx.invoke(add_to_repertoire)
    else:
        click.echo('Done!')


@cli.command()
@click.pass_context
def add_to_care_needs(ctx):
    from app.db.taxonomy import PlantTaxonomy
    from app.db.care import CareNeeds

    click.echo('Updating plant care needs.')
    click.echo('Plant Identification Information')

    while True:
        species = click.prompt(
            'plant species',
            type=str,
            value_proc=lambda x: x.lower()
        )
        if PlantTaxonomy.query(species):
            break
        else:
            click.echo('Species not found. Please provide the correct name.')
            # PlantTaxonomy.advanced_search(species)

    # check if the data is already there.
    r = CareNeeds.query(species)
    update = True if r else False
    if update:
        click.echo('The needs for this species are already added. Will update the needs.')

    click.echo('Plant need information.')
    click.echo('Please enter the scores between 0 and 1.')

    water_freq = click.prompt('watering frequency per day', type=float, default=0.4)
    water_type = click.prompt('watering type', type=click.Choice(['top', 'bottom']), show_choices=True, default='top')
    light_score = click.prompt('score: how much light does the plant need', type=float, default=0.5)
    is_direct_light = click.prompt('does the plant like direct light', type=bool, default=True)
    temp_min = click.prompt('minimum optimal temperature', type=float, default=18.0)
    temp_max = click.prompt('maximum optimal temperature', type=float, default=26.0)
    moistness_score = click.prompt('score: soil moistness', type=float, default=0.5)
    drainage_score = click.prompt('score: pot drainage efficacy need', type=float, default=0.8)
    misting_freq = click.prompt('misting frequency per day', type=float, default=0.03)
    shower_freq = click.prompt('shower frequency per day', type=float, default=0.03)
    fertilisation_freq = click.prompt('fertilization frequency per day', type=float, default=0.03)
    dusting_freq = click.prompt('dusting frequency per day', type=float, default=0.02)

    needs = {
        "water":
            {
                "freq": water_freq,
                "amount": 0.5,
                "watering_type": water_type
            },
        "light":
            {
                "score": light_score,
                "direct": is_direct_light
            },
        "air":
            {
                "temperature":
                    {
                        "min": temp_min,
                        "max": temp_max
                    },
                "humidity": None
            },
        "soil":
            {
                "type": "normal",
                "moistness": moistness_score
            },
        "drainage":
            {
                "score": drainage_score
            },
        "mist":
            {
                "freq": misting_freq
            },
        "shower":
            {
                "freq": shower_freq
            },
        "fertilize":
            {
                "type": "common",
                "freq": fertilisation_freq
            },
        "dust":
            {
                "freq": dusting_freq
            }
    }

    if not update:
        click.echo(F'Adding {species} care needs to database.')
        CareNeeds.add(species=species, needs=needs)
    else:
        click.echo(F'Updating {species} care needs.')
        CareNeeds.update_needs(species=species, needs=needs)
    click.echo('Success!')

    cont = click.prompt('Would you like to add more care needs?',
                        default='n',
                        show_choices=True,
                        type=click.Choice(['y', 'n'])
                        )
    if cont == 'y':
        ctx.invoke(add_to_care_needs)
    else:
        click.echo('Done!')


@cli.command()
@click.option("--path", default=None)
@click.option("--response_type", default='best', type=click.Choice(['best', 'topn']))
@click.option("--topn", default=3)
@click.pass_context
def detect_disease(ctx, path, response_type, topn):
    from plenty.models import disease
    if ctx.obj['DEBUG']:
        click.echo('%s images found in %s' % (len(os.listdir(path)), path))
    res = disease.predict(response_type,
                          topn=topn,
                          path=path
                          )
    click.echo(res)


@cli.command()
@click.option("--path", default=None)
@click.option("--response_type", default='best', type=click.Choice(['best']))
@click.option("--topn", default=3)
@click.pass_context
def detect_species(ctx, path, response_type, topn):
    from plenty.models import species
    if ctx.obj['DEBUG'] and path is not None:
        click.echo('%s images found in %s' % (len(os.listdir(path)), path))
    res = species.predict(response_type,
                          topn=topn,
                          path=path
                          )
    specie = res[0]['scientificName']
    common_name = cn[0] if (cn := res[0]['commonNames']) else str()
    proba = res[0]['proba']
    m = _species_detection_notification(
        specie=specie,
        common_name=common_name,
        proba=proba,
    )
    notify('Plenty Species Detection!', m)


if __name__ == '__main__':
    logger = _init_logger()
    logger.info("\n\n****CLI RUN****")
    cli(obj={})
