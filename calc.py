import matplotlib
matplotlib.use("Agg")

import numpy as np


_LIM_T = -20, 40
_LIM_H = 0, 15000


M = -3. / 1000
H_TRIGGER = 4000.


def calculate(data, t0, h0):
    height = np.array([hi.to('feet').m for hi in data.h if hi.to('feet').m <= _LIM_H[1]])
    temp = np.array([ti.to('degC').m for ti in data.T[:len(height)]])
    dew = np.array([ti.to('degC').m for ti in data.Td[:len(height)]])
    temp_max = [t0 + M * (hi - h0) for hi in height]

    trig_h = np.interp(H_TRIGGER, height, temp)
    trig = trig_h + M * (height - H_TRIGGER)
    trig_0 = trig_h + M * (h0 - H_TRIGGER)

    tol = np.interp(0, np.flip(temp_max-temp, 0), np.flip(height, 0))

    tol_minus_3 = np.interp(0, np.flip(temp_max-temp-3, 0), np.flip(height, 0))

    wind_u = np.array([ti.to('knot').m for ti in data.wind_u[:len(height)]])
    wind_v = np.array([ti.to('knot').m for ti in data.wind_v[:len(height)]])

    return {
        'height': height,
        'temp': temp,
        'dew': dew,
        'temp_max': temp_max,
        'trig': trig,
        'h0': h0,
        't0': t0,
        'trig_0': trig_0,
        'tol': tol,
        'tol_minus_3': tol_minus_3,
        'lim_h': _LIM_H,
        'lim_t': _LIM_T,
        'wind_u': wind_u,
        'wind_v': wind_v,
    }


