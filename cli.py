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
