import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io

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
import numpy as np

import ims


CACHE = cache.CacheManager()
URL = 'http://weather.uwyo.edu/cgi-bin/sounding?region=mideast&TYPE=TEXT%3ALIST&YEAR={date.year}&MONTH={date.month}&FROM={date.day}{hour}&TO={date.day}{hour}&STNM=40179'
FILE_NAME = '/tmp/sounding-{date.year}-{date.month}-{date.day}-{hour}.png'

import matplotlib.image as image

plane_hot = image.imread('plane-hot.png')
plane_cold = image.imread('plane-cold.png')

def get(station):
    buf = _get(station)
    copy = io.BytesIO()
    copy.write(buf)
    copy.seek(0)
    return copy


@CACHE.cache('graph', expire=60*60)
def _get(station):

    logging.info('Starting to calculate graph')

    logging.info('Collecting data from uwyo')
    uwyo_table = _uwyo_data()

    logging.info('Collecting temperatures')
    temp = ims.temp_max(station)

    plt = plot(uwyo_table, temp, station['elevation'])

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return buf.read()


T_LIM = -20, 40
H_LIM = 0, 15000


M = -3. / 1000
H_TRIGGER = 4000.


def plot(data, t0, h0):

    h = np.array([hi.to('feet').m for hi in data.h if hi.to('feet').m <= H_LIM[1]])
    T = np.array([ti.to('degC').m for ti in data.T[:len(h)]])
    Td = np.array([ti.to('degC').m for ti in data.Td[:len(h)]])

    fig = plt.figure(figsize=(6, 10))
    ax = fig.add_subplot(111)
    ax.grid(True)
    ax.set_ylim(*H_LIM)
    ax.set_xlim(*T_LIM)

    # Plot the data using normal plotting functions, in this case using
    # log scaling in Y, as dictated by the typical meteorological plot
    ax.plot(T, h, 'r', label='Temp [C]')
    ax.plot(Td, h, 'b', label='Dew Point [C]')

    t_max = [
        t0 + M * (hi - h0)
        for hi in h
    ]

    # plot temp max
    ax.plot(t_max, h, 'g--', label='Tmax DALR {:.1f} C'.format(t0))

    # plot ground
    ax.plot(T_LIM, [h0, h0], 'brown')

    # calculate trigger temperature
    t_trigger = np.interp(H_TRIGGER, h, T)
    t0_trigger = t_trigger + M * (h0 - H_TRIGGER)
    ax.plot([t_trigger, t0_trigger], [H_TRIGGER, h0], 'r--', label='Trigger {:.1f} C'.format(t0_trigger))

    # calculate TOL and T-3
    TOL = np.interp(0, np.flip(t_max-T, 0), np.flip(h, 0))
    ax.plot([T_LIM[-1]-3], [TOL], "ro", label='TOL {:.0f} ft'.format(TOL), marker=r'^')

    Tminus3 = np.interp(0, np.flip(t_max-T-3, 0), np.flip(h, 0))
    ax.plot([T_LIM[-1]-3], [Tminus3], 'yo', label='T-3 {:.0f} ft'.format(Tminus3), marker=r'^')

    fig.tight_layout()
    fig.legend()
    return fig


_uwyo_col_names = ['pressure', 'height', 'temperature', 'dewpoint', 'relh', 'mixr', 'direction', 'speed', 'thta', 'thte', 'thtv']


def _uwyo_data():
    now = datetime.now()
    hour = '00'
    # get HTML sounding content
    resp = requests.get(URL.format(date=now, hour=hour))
    if resp.status_code != 200:
        logging.error('Got unexpected status from "weather.uwyo.edu: %d: %s', resp.status_code, resp.content)
        raise exceptions.InternalServerError('Failed to get sounding data from "http://weather.uwyo.edu"')

    # parse html sounding content
    page = bs4.BeautifulSoup(resp.content, 'html.parser')
    pre = page.html.find('pre')

    if pre is None:
        logging.error('Failed parsing sounding page: %s' % page)
        raise exceptions.InternalServerError('Failed parsing sounding content')

    table = pre.text

    df = pd.read_fwf(StringIO(table), skiprows=5, usecols=[0, 1, 2, 3, 4, 6, 7], names=_uwyo_col_names)

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

