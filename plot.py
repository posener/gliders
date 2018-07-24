import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import ticker
from matplotlib import transforms
import io
import numpy as np

from beaker import cache
import logging


CACHE = cache.CacheManager()
FILE_NAME = '/tmp/sounding-{date.year}-{date.month}-{date.day}-{hour}.png'


matplotlib.rc('font', family='normal', size=16)


def plot(data):
    buf = _cached(data)
    copy = io.BytesIO()
    copy.write(buf)
    copy.seek(0)
    return copy


@CACHE.cache('plot', expire=60)
def _cached(data):
    logging.info('Drawing plot for %s', data)
    plt = _plot(**data)
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return buf.read()


def _plot(height, temp, dew, temp_max, trig, h0, t0, trig_0, tol, tol_minus_3, cloud_base, lim_h, lim_t, wind_u, wind_v):
    fig = plt.figure(figsize=(6, 10))
    ax = fig.add_subplot(111)
    ax.grid(True)
    ax.set_ylim(*lim_h)
    ax.set_xlim(*lim_t)
    ax.set_xlabel('Temp [C]')
    ax.set_ylabel('Elevation [1000f]')

    ax.yaxis.set_major_formatter(ticker.FuncFormatter(
        lambda y, pos: '%.0f' % (y * 1e-3)))

    # Plot the data using normal plotting functions, in this case using
    # log scaling in Y, as dictated by the typical meteorological plot
    ax.plot(temp, height, 'r', label='Temp [C]')
    ax.plot(dew, height, 'b', label='Dew Point [C]')

    # plot temp max
    ax.plot(temp_max, height, 'g', label='Tmax DALR {:.1f} C'.format(t0))

    # plot ground
    ax.plot(lim_t, [h0, h0], 'brown', label='Ground {:.0f}'.format(h0))

    # calculate trigger temperature
    ax.plot(trig, height, 'g--', label='Trigger {:.1f} C'.format(trig_0))

    # plot TOL and T-3 and cloud base
    ax.plot([lim_t[-1] - 3], [tol], "ro", label='TOL {:.0f} ft'.format(tol), marker=r'^', markersize=16)
    ax.plot([lim_t[-1] - 3], [tol_minus_3], 'yo', label='T-3 {:.0f} ft'.format(tol_minus_3), marker=r'^', markersize=16)
    if cloud_base is not None:
        ax.plot([lim_t[-1] - 3], [cloud_base], 'bo', label='Cloud Base {:.0f} ft'.format(cloud_base), marker=r'^', markersize=16)

    xloc = 0.1
    x_clip_radius = 0.08
    y_clip_radius = 0.08

    x = np.empty_like(height)
    x.fill(xloc)

    # Do barbs plot at this location
    b = ax.barbs(x, height, wind_u, wind_v,
                      transform=ax.get_yaxis_transform(which='tick2'),
                      clip_on=True)

    # Override the default clip box, which is the axes rectangle, so we can have
    # barbs that extend outside.
    ax_bbox = transforms.Bbox([[xloc - x_clip_radius, -y_clip_radius],
                               [xloc + x_clip_radius, 1.0 + y_clip_radius]])
    b.set_clip_box(transforms.TransformedBbox(ax_bbox, ax.transAxes))

    fig.tight_layout()
    fig.legend()
    return fig




