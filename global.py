import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import metpy.calc as mpcalc
from metpy.cbook import get_test_data
from metpy.plots import add_metpy_logo, SkewT
from metpy.units import units
# GFS analysis valid for grid point 10.2 nm / 243 deg from 32.577899,35.179972:
# GFS         12      10      Jun    2018
#    CAPE    791    CIN   -238  Helic  99999     PW     17
#       1  23062  99999  32.50 -35.00  99999  99999
#       2  99999  99999  99999     35  99999  99999
#       3           32.577899,35.179972   12     kt
#       9  10000     69    281    181    256     13
#       4   9750    292    260    166    255     15
#       4   9500    521    246    133    255     15
#       4   9250    754    243     73    257     16
#       4   9000    994    246    -21    262     17
#       4   8500   1491    220    -62    272     20
#       4   8000   2013    190   -101    281     24
#       4   7500   2561    147   -108    285     27
#       4   7000   3139    102   -138    286     27
#       4   6500   3749     57   -201    288     24
#       4   6000   4398     12   -259    287     23
#       4   5500   5090    -40   -261    284     23
#       4   5000   5833    -99   -291    268     22
#       4   4500   6638   -148   -399    257     28
#       4   4000   7518   -210   -404    263     32
#       4   3500   8488   -289   -433    267     32
#       4   3000   9572   -366   -542    266     35
#       4   2500  10815   -435   -635    260     49
#       4   2000  12294   -503   -703    251     65
#       4   1500  14129   -598   -769    248     66
#       4   1000  16601   -692   -818    246     32
#       4    700  18727   -684   -806    234      9
#       4    500  20771   -624   -785     93      7
#       4    300  23989   -542   -831    125      9
#       4    200  26617   -493   -827    107      9
#       4    100  31252   -403   -856     97     19
#       4     70  33709   -348   -863    104     23
#       4     50  36092   -273  99999    108     27
#       4     30  39858   -150  99999    103     41
#       4     20  42962    -92  99999     95     55
#       4     10  48325    -99  99999     96     71

# 1: pressure [mb*10]
# 2: height [m]
# 3: t [C*10]
# 4: td [C*10]
# 5: wind direction [deg]
# 6: wind speed [knots]

col_names = ['x', 'pressure', 'height', 'temperature', 'dewpoint', 'direction', 'speed']


def plot_p_t(data):
    d = _process(data)

    fig = plt.figure()
    skew = SkewT(fig, rotation=45)

    # Plot the data using normal plotting functions, in this case using
    # log scaling in Y, as dictated by the typical meteorological plot
    skew.plot(d.p, d.T, 'r')
    skew.plot(d.p, d.Td, 'g')
    skew.plot_barbs(d.p, d.wind_u, d.wind_v)
    skew.ax.set_ylim(1000, 100)
    skew.ax.set_xlim(-40, 60)

    # Calculate LCL height and plot as black dot
    lcl_pressure, lcl_temperature = mpcalc.lcl(d.p[0], d.T[0], d.Td[0])
    skew.plot(lcl_pressure, lcl_temperature, 'ko', markerfacecolor='black')

    # Calculate full parcel profile and add to plot as black line
    prof = mpcalc.parcel_profile(d.p, d.T[0], d.Td[0]).to('degC')
    skew.plot(d.p, prof, 'k', linewidth=2)

    # Shade areas of CAPE and CIN
    skew.shade_cin(d.p, d.T, prof)
    skew.shade_cape(d.p, d.T, prof)

    # An example of a slanted line at constant T -- in this case the 0
    # isotherm
    skew.ax.axvline(0, color='c', linestyle='--', linewidth=2)

    # Add the relevant special lines
    skew.plot_dry_adiabats()
    skew.plot_moist_adiabats()
    skew.plot_mixing_lines()
    plt.savefig('/tmp/sounding.png')

    return '/tmp/sounding.png'


def plot_h_t(data):
    d = _process(data)

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.grid(True)

    # Plot the data using normal plotting functions, in this case using
    # log scaling in Y, as dictated by the typical meteorological plot
    ax.plot(d.T, d.h, 'r')
    ax.plot(d.Td, d.h, 'g')
    # skew.plot_barbs(d.p, d.wind_u, d.wind_v)
    ax.set_ylim(0, 15000)
    ax.set_xlim(-20, 40)
    #
    # # Calculate LCL height and plot as black dot
    lcl_pressure, lcl_temperature = mpcalc.lcl(d.p[0], d.T[0], d.Td[0])
    ax.plot(lcl_pressure, lcl_temperature, 'ko', markerfacecolor='black')
    #
    # # Calculate full parcel profile and add to plot as black line
    # prof = mpcalc.parcel_profile(d.p, d.T[0], d.Td[0]).to('degC')
    # skew.plot(d.p, prof, 'k', linewidth=2)
    #
    # # Shade areas of CAPE and CIN
    # skew.shade_cin(d.p, d.T, prof)
    # skew.shade_cape(d.p, d.T, prof)
    #
    # # An example of a slanted line at constant T -- in this case the 0
    # # isotherm
    # skew.ax.axvline(0, color='c', linestyle='--', linewidth=2)
    #
    # # Add the relevant special lines
    # skew.plot_dry_adiabats()
    # skew.plot_moist_adiabats()
    # skew.plot_mixing_lines()
    fig.savefig('/tmp/sounding.png')

    return '/tmp/sounding.png'


class Data:

    def __init__(self, h, p, T, Td):
        self.h = h
        self.p = p
        self.T = T
        self.Td = Td
        self.wind_u = None
        self.wind_v = None


def _process(data):
    df = pd.read_fwf(get_test_data(data, as_file_obj=False), skiprows=6, usecols=[1, 2, 3, 4, 5, 6], names=col_names)

    df = df.dropna(
        subset=('temperature', 'dewpoint', 'direction', 'speed'),
        how='all').reset_index(drop=True)

    d = Data(
        h=df['height'].values * units.meter,
        p=df['pressure'].values/10.0 * units.millibar,
        T=df['temperature'].values/10.0 * units.degC,
        Td=df['dewpoint'].values/10.0 * units.degC,
    )
    d.h = d.h.to('feet')
    d.wind_u, d.wind_v = mpcalc.get_wind_components(
        df['speed'].values * units.knots,
        df['direction'].values * units.degrees)

    return d

