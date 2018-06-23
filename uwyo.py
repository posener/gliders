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


CACHE = cache.CacheManager()
_URL = 'http://weather.uwyo.edu/cgi-bin/sounding?region=mideast&TYPE=TEXT%3ALIST&YEAR={date.year}&MONTH={date.month}&FROM={date.day}{hour}&TO={date.day}{hour}&STNM=40179'
_COL_NAMES = ['pressure', 'height', 'temperature', 'dewpoint', 'relh', 'mixr', 'direction', 'speed', 'thta', 'thte', 'thtv']


def data():
    now = datetime.now()

    # first try noon measurements
    url = _URL.format(date=now, hour='12')
    data = _uwyo_data_get(url)
    if data is not None:
        return data, 'noon'

    # if no noon measurements available, return the midnight measurements
    url = _URL.format(date=now, hour='00')
    data = _uwyo_data_get(url)
    if data is not None:
        return data, 'midnight'

    raise exceptions.NotFound('No sounding data available from today')


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

