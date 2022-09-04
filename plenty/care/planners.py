import copy
from abc import ABC, abstractmethod
import datetime as dt
import logging
from functools import wraps
from typing import Union, Tuple, List
import numpy as np

from app.db.repertoire import PlantUnit
from plenty.climate import ClimateConditions
from plenty.care import optimisers


# TODO: seems like imputer doesn't have any impact, check why?


logger = logging.getLogger("app.care.planners")


def dates_to_binary(hist: List[dt.date],
                    from_date: dt.date,
                    to_date: dt.date
                    ):
    return [
        1 if from_date + dt.timedelta(days=i) in hist else 0
        for i in range((to_date - from_date).days)
    ]


def _impute_detection(func):
    @wraps(func)
    def detect_and_run(h: List[int], *args, **kwargs):
        if not any(h):
            logger.debug('applying imputation.')
            return func(h, *args, **kwargs)
        else:
            logger.debug('skipping imputation.')
            return h
    return detect_and_run


@_impute_detection
def constant_imputer(h: List[int], value: int = 0):
    return [
        value if i == 0 else i
        for i in h
    ]


@_impute_detection
def random_need_imputer(h: List[int], need: float):
    return np.random.binomial(1, need, len(h)).tolist()


@_impute_detection
def random_factor_need_imputer(h: List[int], need: float, factor: float):
    return np.random.binomial(1, need * factor, len(h)).tolist()


@_impute_detection
def factor_change_imputer(h: List[int], need: float, factor: float):
    return [
        [need * factor] * (len(h) - 1), 1
    ]


class Planner(ABC):

    today = dt.date.today()
    lookback = 15

    @classmethod
    @abstractmethod
    def step(cls, *args, **kwargs):
        """
        Plan the care for a date.

        Parameters
        ----------
        args
        kwargs

        Returns
        -------
        int
            1 if plant should be cared on care type, 0 if not.
        """
        pass

    @classmethod
    def plan(cls,
             plant: PlantUnit,
             care_type: str,
             start_date: dt.date = None,
             n_days: int = 10,
             optimise: bool = True,
             impute: bool = False
             ) -> Tuple[List, List]:
        """
        Plan the care schedule for the next n days.

        Parameters
        ----------
        plant: PlantUnit
            plant
        care_type: str
            care type name
        start_date: date
            start date
        n_days: int
            n days ahead to plan schedule
        optimise: bool
            optimise schedule
        impute: bool
            apply imputation

        Returns
        -------
        Tuple[List[str], List[int]]
            dates, care plan results
        """
        logger.info('running planner.')
        if start_date is None:
            start_date = cls.today
        dates = list()
        results = list()
        plant_copy = copy.deepcopy(plant)
        for n_day in range(1, n_days+1):
            date = start_date + dt.timedelta(days=n_day)
            logger.debug(f'planning for {str(date)}')

            result = cls.step(
                plant_copy,
                care_type,
                date,
                optimise=optimise,
                impute=False if n_day == 1 else impute  # don't impute the first day.
                )

            if result == 1:
                plant_copy.hist.hist.append(
                    (plant_copy.id, care_type, str(date))
                )

            logger.debug(F'to {care_type}: {result}')
            dates.append(date)
            results.append(result)
        return dates, results


class Bernoulli(Planner):
    planner_short_name = 'bayes'

    @classmethod
    def step(cls, plant: PlantUnit, care_type: str, date: Union[dt.date], optimise=True, impute: bool = False):
        freq = plant.needs.get(care_type, {}).get('freq', 0.05)
        if optimise:
            excon = ClimateConditions.get()
            logger.debug('optimisation is on.')
            n = optimisers.get(care_type)\
                .opt(freq, plant.needs, plant.conditions, excon)
        else:
            logger.debug('optimisation is off.')
            n = freq

        h = dates_to_binary(
            plant.hist(care_type),
            from_date=date - dt.timedelta(cls.lookback),
            to_date=date
        )

        logger.debug(F'need: {n}')
        logger.debug(F'frequency : {freq}')
        logger.debug(F'history : {h}')
        if impute:
            h = random_factor_need_imputer(h, n, 0.8)
        if h:
            mu = np.mean(h)
            mu = round(float(mu), 3)
        else:
            mu = 0
        p = min(max(n - mu, 0), 1)
        logger.debug(F'mu : {mu}')
        logger.debug(F'proba : {p}')
        if 1 > p > 0:
            return int(np.random.binomial(1, p))
        else:
            return int(p)


class NaiveLookback(Planner):
    planner_short_name = 'naive'

    @classmethod
    def step(cls, plant: PlantUnit, care_type: str, date: Union[dt.date], optimise=True, impute: bool = False):
        freq = plant.needs.get(care_type, {}).get('freq', 0.05)
        if optimise:
            logger.debug('optimisation is on.')
            excon = ClimateConditions.get()
            n = optimisers.get(care_type) \
                .opt(freq, plant.needs, plant.conditions, excon)
        else:
            logger.debug('optimisation is off.')
            n = freq

        h = dates_to_binary(
            plant.hist(care_type),
            from_date=date - dt.timedelta(cls.lookback),
            to_date=date
        )

        logger.debug(F'need: {n}')
        logger.debug(F'frequency : {freq}')
        logger.debug(F'history : {h}')
        if impute:
            h = random_need_imputer(h, n)
        if h:
            mu = np.mean(h)
            mu = round(float(mu), 3)
        else:
            mu = 0
        logger.debug(F'mu : {mu}')
        if mu < n:
            return 1
        elif mu == n:
            return 1 - h[-1]
        else:
            return 0


class DynamicLookback(Planner):
    planner_short_name = 'dynamic'

    @classmethod
    def step(cls, plant: PlantUnit, care_type: str, date: Union[dt.date], optimise=True, impute: bool = False):
        freq = plant.needs.get(care_type, {}).get('freq', 0.05)
        if optimise:
            logger.debug('optimisation is on.')
            excon = ClimateConditions.get()
            n = optimisers.get(care_type) \
                .opt(freq, plant.needs, plant.conditions, excon)
        else:
            logger.debug('optimisation is off.')
            n = freq

        lookback = round(1 / n)
        h = dates_to_binary(
            plant.hist(care_type),
            from_date=date - dt.timedelta(lookback),
            to_date=date
        )

        logger.debug(F'need: {n}')
        logger.debug(F'frequency : {freq}')
        logger.debug(F'history : {h}')
        if impute:
            h = random_need_imputer(h, n)
        if h:
            mu = np.mean(h)
            mu = round(float(mu), 3)
        else:
            mu = 0
        logger.debug(F'mu : {mu}')
        if mu < n:
            return 1
        elif mu == n:
            return 1 - h[-1]
        else:
            return 0


def get_planner(name):
    """
    Get planner object with name.
    Parameters
    ----------
    name: str
        planner name

    Returns
    -------
    Planner
    """
    res = list(filter(lambda x: x.planner_short_name == name,
                      Planner.__subclasses__())
               )
    if res:
        return res.pop()
    else:
        raise ValueError(F'no planner found with name : {name}')
