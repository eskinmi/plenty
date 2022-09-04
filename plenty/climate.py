import datetime
import logging
import meteostat

from plenty.api.openweathermap import get_point
from plenty.utils import get_user_info


# TODO: setup advanced adjustments from outdoor temp to indoor temp.

logger = logging.getLogger("app.climate")


# noinspection PyArgumentList
def _fetch_daily_climate(end_time: datetime.time = None,
                         days_back: int = 15
                         ):
    ui = get_user_info()
    city, state_code, country_code = ui.get('city'), ui.get('state_code'), ui.get('country_code')
    if not any([city, state_code, country_code]):
        logger.debug('user has no location information.')
    lat, lon = get_point(city, state_code, country_code)
    point = meteostat.Point(lat, lon)
    if end_time is None:
        end_time = datetime.datetime.now()\
            .replace(hour=0, minute=0, second=0, microsecond=0)
    daily_loader = meteostat.Daily(
        point,
        end_time - datetime.timedelta(days=days_back),
        end_time
    )
    return daily_loader.fetch()


def _estimate_indoor_temp_from_outdoor_temp(t: float):
    if t < 17:
        return 19.0
    elif 28 >= t >= 25:
        return 21.0
    elif t > 28:
        return 22.0
    else:
        return 20.0


class ClimateConditions:
    days_back = 15
    cond = None

    @classmethod
    def get(cls):
        if cls.cond is None:
            logger.debug('climate data does not exist.')
            data = _fetch_daily_climate()
            if data.empty:
                logger.warning('climate data returned empty response!')
                cls.cond = {}
            else:
                cond = data[['tavg', 'tmin', 'tmax', 'tsun']]\
                    .sort_index(ascending=True)\
                    .to_dict(orient='list')
                cond['t_avg_ind'] = list(map(
                    lambda x: _estimate_indoor_temp_from_outdoor_temp(x),
                    cond['tavg']
                ))
                cls.cond = cond
        else:
            logger.info('climate data exists, returning existing data.')
        return cls.cond
