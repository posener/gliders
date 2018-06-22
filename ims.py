import re
import logging
import requests
import bs4
from beaker import cache


CACHE = cache.CacheManager()
_IMS_AUTH = {'Authorization': 'ApiToken 1a901e45-9028-44ff-bd2c-35e82407fb9b'}

_session = requests.Session()
_session.headers = _IMS_AUTH

_DIGITS = re.compile(r'\d+')


def temp_max(station):
    return _temp_max(station['temp_max_id'])


@CACHE.cache('temp_max', expire=60*60*1)
def _temp_max(station_id):
    resp = requests.post(
        'http://www.ims.gov.il/IMS/Pages/IsrCitiesTodayForeCast.aspx',
        data={
            'LangId': '1',
            'LocationId': str(station_id),
            'CF': 'C',
        }
    )
    resp.raise_for_status()
    page = bs4.BeautifulSoup(resp.content, 'html.parser')
    txt = page.find(id='MaxTempDuringDayVal').text
    return int(_DIGITS.match(txt).group())


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


