from abc import ABC, abstractmethod
import logging
import numpy as np
import math

""" 
Care optimisations based on factors like weather, light etc. 

Some abbreviations used in this script:
    tmw: temperature weight
    dhw: daylight hours weight
    lgw: light score weight
    drw: drainage score weight
"""

logger = logging.getLogger('app.care.optimisers')

# _ = CareNeeds.get()  # TODO: check if we need to do this load here.


def mk_recency_weights(length: int = 15):
    return np.log10(np.linspace(1, length, length))


def optimal_temperature_center(needs):
    """
    Find the optimal temperature center.

    Parameters
    ----------
    needs: dict
        plant needs

    Returns
    -------
    Union[int, float]
    """
    if t := needs['air']['temperature']:
        return t['min'] + (t['max'] - t['min']) / 2
    else:
        return 18


def mean_weighted_temperature(external_cond, indoor=True):
    """
    Calculate mean recency weighted temperature.

    Parameters
    ----------
    external_cond: dict
        external conditions
    indoor: bool
        True if indoor plant, otherwise False

    Returns
    -------
    Union[float, None]
    """
    if not indoor:
        t_arr = external_cond.get('tavg')
    else:
        t_arr = external_cond.get('t_avg_ind')
    if t_arr:
        wgt = mk_recency_weights(len(t_arr))
        t_mu = float(
            np.sum(np.array(t_arr) * wgt) / np.sum(wgt)
        )
    else:
        t_mu = None
    return t_mu


class CareOpt(ABC):
    """
    Care type optimizer. This module is the main
    class for all optimizers for care_type such as;
    water, mist, dust; given the external factors like
    weather conditions, drainage efficiency of the pot,
    light conditions etc.

    Parameters
    ----------
    base_tmw: Union[float, int]
        Base Temperature Weight:
            The weight to be applied to the condition
            frequency given the difference in actual
            and optimal temperature.
    base_dhw: Union[float, int]
        Base Daylight Hours Weight
            The weight to be applied to the condition
            frequency given the difference in actual
            and optimal daylight hours.
    base_lgw: Union[float, int]
        Base Light Weight
            The weight to be applied to the condition
            frequency given the difference in actual
            and optimal light conditions.
    base_drw: Union[float, int]
        Base Drainage Weight
            The weight to be applied to the condition
            frequency given the difference in actual
            and optimal drainage efficiency.

    """

    def __init__(self,
                 base_tmw=None,
                 base_dhw=None,
                 base_lgw=None,
                 base_drw=None
                 ):
        self.base_tmw = 1.0 if base_tmw is None else base_tmw
        self.base_dhw = 1.0 if base_dhw is None else base_dhw
        self.base_lgw = 1.0 if base_lgw is None else base_lgw
        self.base_drw = 1.0 if base_drw is None else base_drw

    @property
    @abstractmethod
    def care_type(self):
        pass

    @abstractmethod
    def opt(self, *args, **kwargs):
        pass


class NoOpt(CareOpt):
    care_type = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.info('inside NoOpt. returning freq directly.')

    def opt(self, freq, *args, **kwargs):
        return freq
        

class WaterOpt(CareOpt):
    care_type = 'water'
    
    def __init__(self):
        super().__init__()

    def set_temperature_weight(self, needs, plant_cond, external_cond):
        """
        Calculate temperature weight factor.

        Parameters
        ----------
        needs: dict:
            plenty.repertoire.PlantUnit.needs
        plant_cond: dict
            plenty.repertoire.PlantUnit.conditions
        external_cond: dict
            plenty.climate.ClimateConditions

        Returns
        -------
        float
            temperature weight factor
        """
        t_o = optimal_temperature_center(needs)
        t_m = mean_weighted_temperature(external_cond, plant_cond.get('indoor', True))
        if t_m is None:
            t_m = t_o
        d = t_o - t_m
        w = 1 + math.log(abs(d), 10)
        if d > 0:
            self.base_tmw = w
        else:
            self.base_tmw = 1/w

    def set_drainage_weight(self, needs, plant_cond):
        """
        Calculate the drainage weight factor.
        If the drainage is already good, no positive weight

        Parameters
        ----------
        needs: dict:
            plenty.repertoire.PlantUnit.needs
        plant_cond: dict
            plenty.repertoire.PlantUnit.conditions

        Returns
        -------
        float
            drainage factor
        """
        if plant_cond.get('drainage', {}).get('score', 0.3) >= \
                needs.get('drainage', {}).get('score', 0.3):
            logger.debug('setting drainage weight to 1.0')
            self.base_drw = 1.0
        else:
            pass
            # drainage is not goog enough
            # advice should be given to not over-water or to re-pot.

    def opt(self, freq, needs, plant_cond, external_cond):
        self.set_temperature_weight(needs, plant_cond, external_cond)
        self.set_drainage_weight(needs, plant_cond)
        logger.debug(F'freq : {freq}')
        logger.debug(
            """
            mist opt weights:
                temperature: {tmw}
                drainage: {drw}
                light: {lgw}
                daylight hours: {dhw}
            """.format(
                tmw=self.base_tmw,
                drw=self.base_drw,
                lgw=self.base_lgw,
                dhw=self.base_dhw,
            )
        )
        return freq * \
            self.base_tmw *\
            self.base_drw * \
            self.base_lgw *\
            self.base_dhw


class MistOpt(CareOpt):
    care_type = 'mist'

    def __init__(self):
        super().__init__()

    def set_temperature_weight(self, needs, plant_cond, external_cond):
        """
        Calculate temperature weight factor.

        Parameters
        ----------
        needs: dict:
            plenty.repertoire.PlantUnit.needs
        plant_cond: dict
            plenty.repertoire.PlantUnit.conditions
        external_cond: dict
            plenty.climate.ClimateConditions

        Returns
        -------
        float
            temperature weight factor
        """
        t_o = optimal_temperature_center(needs)
        t_m = mean_weighted_temperature(external_cond, plant_cond.get('indoor', True))
        if t_m is None:
            t_m = t_o
        d = t_o - t_m
        w = 1 + math.log(abs(d), 10)
        if d > 0:
            self.base_tmw = w
        else:
            self.base_tmw = 1 / w

    def set_light_weight(self, needs, plant_cond):
        """
        Calculate the light score weight for
        misting of the plant.

        Parameters
        ----------
        needs: dict:
            plenty.repertoire.PlantUnit.needs
        plant_cond: dict
            plenty.repertoire.PlantUnit.conditions

        Returns
        -------
        float
            light weight factor
        """
        need = needs.get('light', {}).get('score', 0.5)
        has = plant_cond.get('light', {}).get('score', 0.5)
        if need < has:
            self.base_lgw *= (has / need)

    def opt(self, freq, needs, plant_cond, external_cond):
        self.set_temperature_weight(needs, plant_cond, external_cond)
        self.set_light_weight(needs, plant_cond)
        logger.debug(F'freq : {freq}')
        logger.debug(
            """
            mist opt weights:
                temperature: {tmw}
                drainage: {drw}
                light: {lgw}
                daylight hours: {dhw}
            """.format(
                tmw=self.base_tmw,
                drw=self.base_drw,
                lgw=self.base_lgw,
                dhw=self.base_dhw,
            )
        )
        return freq * \
            self.base_tmw *\
            self.base_drw *\
            self.base_lgw *\
            self.base_dhw


def get(care_type: str):
    if matches := list(filter(lambda x: x.care_type == care_type, CareOpt.__subclasses__())):
        Opt = matches.pop()
        return Opt()
    else:
        logger.debug(
            """
            Couldn't find a matching care optimizer.
            Returning NoOpt.
            """
        )
        return NoOpt()
