import time
import matplotlib
matplotlib.use("Agg")

from beaker import cache
import logging
from datetime import datetime
from datetime import timedelta
import requests
from werkzeug import exceptions
from io import StringIO
import pandas as pd
from metpy.units import units
import metpy.calc as mpcalc

import timeformat


class NoSoundingDataException(Exception):
    pass


class InvalidTimeRangeException(Exception):
    pass


CACHE = cache.CacheManager()
_URL = 'https://rucsoundings.noaa.gov/get_soundings.cgi?data_source=GFS&start_year={date.year}&start_month_name={month}&start_mday={date.day}&start_hour={date.hour}&start_min=0&n_hrs=1.0&fcst_len=shortest&airport=32.6%2C35.23&text=Ascii%20text%20%28GSD%20format%29&hydrometeors=false&startSecs={start_sec}&endSecs={end_sec}'
_COL_NAMES = ['cape', 'pressure', 'height', 'temperature', 'dewpoint', 'direction', 'speed']
_MIN_SOUNDING_LEN = 5


def data(date):
    date = data_time(date)

    start_sec = int(time.mktime(date.timetuple()))
    end_sec = start_sec + 3600
    month = date.strftime("%b")

    # first try noon measurements
    url = _URL.format(date=date, month=month, start_sec=start_sec, end_sec=end_sec)
    data = _uwyo_data_get(url)
    if data is not None:
        return data, date

    logging.warning('No NOAA sounding data data for date %s', date)
    raise NoSoundingDataException()


def data_time(date):
    if date > datetime.now() + timedelta(days=5):
        raise InvalidTimeRangeException()

    # round hours to a multiple of 3
    date -= timedelta(hours=date.hour % 3, minutes=date.minute, seconds=date.second)

    return date


@CACHE.cache('noaa-data', expire=60*60)
def _uwyo_data_get(url):
    logging.info('Collecting data from NOAA')
    # get HTML sounding content
    resp = requests.get(url)
    if resp.status_code != 200:
        logging.error('Got unexpected status from "noaa: %d: %s', resp.status_code, resp.content)
        raise exceptions.InternalServerError('Failed to get sounding data from "http://weather.uwyo.edu"')

    table = resp.text

    df = pd.read_fwf(StringIO(table), skiprows=6, usecols=[1, 2, 3, 4, 5, 6], names=_COL_NAMES)

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
        p=df['pressure'].values / 10.0 * units.hPa,
        T=df['temperature'].values / 10.0 * units.degC,
        Td=df['dewpoint'].values / 10.0 * units.degC,
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

