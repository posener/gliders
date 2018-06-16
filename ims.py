import requests
from beaker import cache


CACHE = cache.CacheManager()
_IMS_AUTH = {'Authorization': 'ApiToken 1a901e45-9028-44ff-bd2c-35e82407fb9b'}


_session = requests.Session()
_session.headers = _IMS_AUTH


def temp_max(station):
    return _weather(station['id'])['TDmax']['value']


@CACHE.cache('weather', expire=60*60*1)
def _weather(station_id):
    data = _session.get('https://api.ims.gov.il/v1/envista/stations/{}/data/latest'.format(station_id)).json()
    return {item['name']: item for item in data['data'][0]['channels']}


