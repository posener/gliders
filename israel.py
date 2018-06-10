import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io

import yaml
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

import ims



CACHE = cache.CacheManager()
URL = 'http://weather.uwyo.edu/cgi-bin/sounding?region=mideast&TYPE=TEXT%3ALIST&YEAR={date.year}&MONTH={date.month}&FROM={date.day}{hour}&TO={date.day}{hour}&STNM=40179'
FILE_NAME = '/tmp/sounding-{date.year}-{date.month}-{date.day}-{hour}.png'

STATIONS = yaml.load(open('stations.yaml'))


def get(station_name='Megido'):
    try:
        station = STATIONS[station_name]
    except KeyError:
        raise exceptions.NotFound('Station not found: {}'.format(station))

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
    temp_max = _temp_max(station['id'])

    plt = plot(uwyo_table, temp_max, station['elevation'])

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return buf.read()


X_LIM = -20, 40


def plot(uwyo_data, temp_max, ground):
    fig = plt.figure(figsize=(6, 10))
    ax = fig.add_subplot(111)
    ax.grid(True)
    ax.set_ylim(0, 15000)
    ax.set_xlim(X_LIM)

    # Plot the data using normal plotting functions, in this case using
    # log scaling in Y, as dictated by the typical meteorological plot
    ax.plot(uwyo_data.T, uwyo_data.h, 'r')
    ax.plot(uwyo_data.Td, uwyo_data.h, 'g')

    # plot temp max
    ax.plot(
        [temp_max, temp_max-10*15],
        [ground, ground+10*5000],
        'k--o'
    )

    # plot ground
    ax.plot(X_LIM, [ground, ground], 'brown')

    # skew.plot_barbs(uwyo_data.p, uwyo_data.wind_u, uwyo_data.wind_v)
    #
    # # Calculate LCL height and plot as black dot
    # lcl_pressure, lcl_temperature = mpcalc.lcl(uwyo_data.p[0], uwyo_data.T[0], uwyo_data.Td[0])
    # ax.plot(lcl_pressure, lcl_temperature, 'ko', markerfacecolor='black')
    #
    # # Calculate full parcel profile and add to plot as black line
    # prof = mpcalc.parcel_profile(uwyo_data.p, uwyo_data.T[0], uwyo_data.Td[0]).to('degC')
    # skew.plot(uwyo_data.p, prof, 'k', linewidth=2)
    #
    # # Shade areas of CAPE and CIN
    # skew.shade_cin(uwyo_data.p, uwyo_data.T, prof)
    # skew.shade_cape(uwyo_data.p, uwyo_data.T, prof)
    #
    # # An example of a slanted line at constant T -- in this case the 0
    # # isotherm
    # skew.ax.axvline(0, color='c', linestyle='--', linewidth=2)
    #
    # # Add the relevant special lines
    # skew.plot_dry_adiabats()
    # skew.plot_moist_adiabats()
    # skew.plot_mixing_lines()
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


def _temp_max(station_id):
    return _weather(station_id)['TDmax']['value']


@CACHE.cache('weather', expire=60*60*1)
def _weather(station_id):
    data = ims.session.get('https://api.ims.gov.il/v1/envista/stations/{}/data/latest'.format(station_id)).json()
    return {item['name']: item for item in data['data'][0]['channels']}


