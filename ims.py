import re
import logging
from datetime import datetime
import requests
import bs4
from beaker import cache


CACHE = cache.CacheManager()
_IMS_AUTH = {'Authorization': 'ApiToken 1a901e45-9028-44ff-bd2c-35e82407fb9b'}

_session = requests.Session()
_session.headers = _IMS_AUTH

_DIGITS = re.compile(r'\d+')
_DATE = re.compile(r'(\d\d)/(\d\d)')


class NoForecastForDateException(Exception):
    pass


def temp_max(station):
    return temp_forecast(station, _today())


def temp_forecast(station, date):
    station_id = station['temp_max_id']
    forecast = _temp_forecast(station_id)
    if date not in forecast:
        logging.warning('No ims data for station %s date %s. available: %s', station_id, date, forecast.keys())
        raise NoForecastForDateException()
    return forecast[date]


@CACHE.cache('temp_forecast', expire=60*60)
def _temp_forecast(station_id):
    logging.info('Collecting temperature forecast from IMS for %d', station_id)
    resp = requests.get('https://ims.gov.il/he/full_forecast_data/{}'.format(station_id))
    resp.raise_for_status()
    data = resp.json()

    forecast = {}

    for date_text, date_forecast in data.iteritems():
        # forecast_data contains [min_temperature_of_day, max_temperature_of_day] as strings
        temp_max = int(date_forecast['daily']['maximum_temperature'])
        forecast_date = datetime.strptime(date_text, '%Y-%m-%d')
        forecast[forecast_date] = temp_max

    return forecast

def _today():
    now = datetime.now()
    return datetime(year=now.year, month=now.month, day=now.day)