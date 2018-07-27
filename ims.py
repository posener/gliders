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
    return _temp_max(station['temp_max_id'])


def temp_forecast(station, date):
    station_id = station['temp_max_id']

    # if today, use temp_max of today
    if _same_day(datetime.now(), date):
        return _temp_max(station_id)

    for forecast_date, temp in _temp_forecast(station_id):
        if _same_day(date, forecast_date):
            return temp

    logging.warning('No ims data for station %s date %s', station_id, date)
    raise NoForecastForDateException()


@CACHE.cache('temp_max', expire=60*60)
def _temp_max(station_id):
    logging.info('Collecting temperatures from IMS')
    resp = requests.post(
        'http://www.ims.gov.il/IMS/Pages/IsrCitiesTodayForeCast.aspx',
        data={
            'LangId': '2',
            'LocationId': str(station_id),
            'CF': 'C',
        }
    )
    resp.raise_for_status()
    page = bs4.BeautifulSoup(resp.content, 'html.parser')
    txt = page.find(id='MaxTempDuringDayVal').text
    return int(_DIGITS.match(txt).group())


@CACHE.cache('temp_forecast', expire=60*60)
def _temp_forecast(station_id):
    logging.info('Collecting temperature forecast from IMS')
    resp = requests.post(
        'http://www.ims.gov.il/IMS/Pages/IsrCitiesForeCast.aspx',
        data={
            'LangId': '2',
            'LocationId': str(station_id),
            'align': 'left',
            'DayAndDate': 'Date',
            'WeatherAndTemprature': 'temperature',
            'CF': 'C',
        }
    )
    resp.raise_for_status()
    page = bs4.BeautifulSoup(resp.content, 'html.parser')

    forecast = []

    forecast_texts = page.find_all(**{'class': 'HPWarningsRegSmallText'})
    forecast_dates = page.find_all(**{'class': 'HPWarningsRegText'})
    for forecast_text, date_text in zip(forecast_texts, forecast_dates):
        forecast_data = _DIGITS.findall(forecast_text.text)
        # forecast_data contains [min_temperature_of_day, max_temperature_of_day] as strings
        temp_max = int(forecast_data[1])
        forecast_date_text = _DATE.findall(date_text.text)[0]
        forecast_date = datetime(
            year=datetime.now().year,
            month=int(forecast_date_text[1]),
            day=int(forecast_date_text[0]),
            hour=12,
        )
        forecast.append((forecast_date, temp_max))

    return forecast


@CACHE.cache('temp_latest', expire=60*60*1)
def temp_latest(station_id):
    data = _session.get(
        'https://api.ims.gov.il/v1/envista/stations/{station_id}/data/daily'.format(
            station_id=station_id,
        )).json()['data']

    temp = 0
    for item in data:
        for channel in item['channels']:
            if channel['name'] == 'TDmax':
                logging.info('TMax: %f', channel['value'])
                temp = max(temp, channel['value'])
                break
    return temp


def _same_day(d1, d2):
    return d1.year == d2.year and d1.month == d2.month and d1.day == d2.day
