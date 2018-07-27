import matplotlib
matplotlib.use("Agg")

from beaker import cache
import logging
from datetime import datetime
import requests
from werkzeug import exceptions
from StringIO import StringIO
import pandas as pd
import bs4
from metpy.units import units
import metpy.calc as mpcalc


class NoSoundingDataException(Exception): pass


CACHE = cache.CacheManager()
_URL = 'http://weather.uwyo.edu/cgi-bin/sounding?region=mideast&TYPE=TEXT%3ALIST&YEAR={date.year}&MONTH={date.month}&FROM={date.day:02d}{date.hour:02d}&TO={date.day:02d}{date.hour:02d}&STNM=40179'
_COL_NAMES = ['pressure', 'height', 'temperature', 'dewpoint', 'relh', 'mixr', 'direction', 'speed', 'thta', 'thte', 'thtv']
_MIN_SOUNDING_LEN = 5


def data():
    date = datetime.now()
    date = date.replace(hour=12)

    # first try noon measurements
    url = _URL.format(date=date)
    data = _uwyo_data_get(url)
    if data is not None:
        return data, date

    # if no noon measurements available, return the midnight measurements
    date = date.replace(hour=0)
    url = _URL.format(date=date)
    data = _uwyo_data_get(url)
    if data is not None:
        return data, date

    raise NoSoundingDataException()


@CACHE.cache('uwyo-data', expire=60*60)
def _uwyo_data_get(url):
    logging.info('Collecting data from UWYO')
    # get HTML sounding content
    resp = requests.get(url)
    if resp.status_code != 200:
        logging.error('Got unexpected status from "weather.uwyo.edu: %d: %s', resp.status_code, resp.content)
        raise exceptions.InternalServerError('Failed to get sounding data from "http://weather.uwyo.edu"')

    # parse html sounding content
    page = bs4.BeautifulSoup(resp.content, 'html.parser')
    try:
        pre = page.html.find('pre')
    except AttributeError:
        return None

    if pre is None:
        logging.error('Failed parsing sounding page: %s' % page)
        raise exceptions.InternalServerError('Failed parsing sounding content')

    table = pre.text

    df = pd.read_fwf(StringIO(table), skiprows=5, usecols=[0, 1, 2, 3, 4, 6, 7], names=_COL_NAMES)

    df = df.dropna(
        subset=('temperature', 'dewpoint', 'direction', 'speed'),
        how='all').reset_index(drop=True)

    if any((
        len(df['height']) < _MIN_SOUNDING_LEN,
        len(df['temperature']) < _MIN_SOUNDING_LEN,
        len(df['pressure']) < _MIN_SOUNDING_LEN,
        len(df['dewpoint']) < _MIN_SOUNDING_LEN,
    )):
        return None

    d = Data(
        h=df['height'].values * units.meter,
        p=df['pressure'].values * units.hPa,
        T=df['temperature'].values * units.degC,
        Td=df['dewpoint'].values * units.degC,
    )
    d.h = d.h.to('feet')
    d.wind_u, d.wind_v = mpcalc.get_wind_components(
        df['speed'].values * units.knots,
        df['direction'].values * units.degrees)

    return d


class Data:

    def __init__(self, h, p, T, Td):
        self.h = h
        self.p = p
        self.T = T
        self.Td = Td
        self.wind_u = None
        self.wind_v = None

