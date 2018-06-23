import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io

from beaker import cache
import logging
import numpy as np

import ims
import uwyo
import calc


CACHE = cache.CacheManager()
FILE_NAME = '/tmp/sounding-{date.year}-{date.month}-{date.day}-{hour}.png'

import matplotlib.image as image

plane_hot = image.imread('plane-hot.png')
plane_cold = image.imread('plane-cold.png')


def plot(station):
    buf = _cached(station)
    copy = io.BytesIO()
    copy.write(buf)
    copy.seek(0)
    return copy


@CACHE.cache('plot', expire=60)
def _cached(station):
    logging.info('Calculating plot for %s', station['station_id'])
    uwyo_table, time = uwyo.data()
    temp = ims.temp_max(station)
    data = calc.calculate(uwyo_table, temp, station['elevation'])
    plt = _plot(**data)
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return buf.read()


def _plot(height, temp, dew, temp_max, trig, h0, t0, trig_0, tol, tol_minus_3, lim_h, lim_t):
    fig = plt.figure(figsize=(6, 10))
    ax = fig.add_subplot(111)
    ax.grid(True)
    ax.set_ylim(*lim_h)
    ax.set_xlim(*lim_t)

    # Plot the data using normal plotting functions, in this case using
    # log scaling in Y, as dictated by the typical meteorological plot
    ax.plot(temp, height, 'r', label='Temp [C]')
    ax.plot(dew, height, 'b', label='Dew Point [C]')

    # plot temp max
    ax.plot(temp_max, height, 'g', label='Tmax DALR {:.1f} C'.format(t0))

    # plot ground
    ax.plot(lim_t, [h0, h0], 'brown')

    # calculate trigger temperature
    ax.plot(trig, height, 'g--', label='Trigger {:.1f} C'.format(trig_0))

    # calculate TOL and T-3
    ax.plot([lim_t[-1] - 3], [tol], "ro", label='TOL {:.0f} ft'.format(tol), marker=r'^')

    ax.plot([lim_t[-1] - 3], [tol_minus_3], 'yo', label='T-3 {:.0f} ft'.format(tol_minus_3), marker=r'^')

    fig.tight_layout()
    fig.legend()
    return fig




