import logging
import sys
from datetime import datetime

import flask

import ims
import uwyo
import calc
import plot
import stations


logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

app = flask.Flask(__name__)


DEFAULT_LOCATION = 'Megido'


@app.route('/', methods=['GET'])
def index():
    uwyo_table, data_time = uwyo.data()

    locations = []
    for loc in stations.all():
        station = stations.get(loc)
        locations.append({
            'name': loc,
            'selected': False,
            'data': calc.calculate(uwyo_table, ims.temp_max(station), station['elevation'])
        })
    max_tol = float(max(loc['data']['tol'] for loc in locations))

    for loc in locations:
        loc['tol_percent'] = loc['data']['tol'] / max_tol * 100

    return flask.render_template(
        'index.html',
        location=None,
        hour=datetime.now().hour,
        locations=locations,
        data_time=data_time,
    )


@app.route('/locations/<location_name>', methods=['GET'])
def site(location_name):
    _, data_time = uwyo.data()
    locations = [
        {'name': loc, 'selected': loc == location_name}
        for loc in stations.all()
    ]

    return flask.render_template(
        'location.html',
        location=location_name,
        hour=datetime.now().hour,
        locations=locations,
        data_time=data_time,
    )


@app.route('/sounding/<location_name>.png', methods=['GET'])
def sounding(location_name):
    location_name = location_name.split('-')[0]
    station = stations.get(location_name)
    uwyo_table, time = uwyo.data()
    temp = ims.temp_max(station)
    data = calc.calculate(uwyo_table, temp, station['elevation'])
    return flask.send_file(plot.plot(data), mimetype='image/png')


@app.context_processor
def level():
    def level(percent):
        if percent <= 25:
            return 'danger'
        if percent <= 50:
            return 'warning'
        if percent <= 75:
            return 'info'
        return 'success'
    return {'level': level}


SOUNDING_URL = 'https://rucsoundings.noaa.gov/gwt/soundings/get_soundings.cgi?airport={lat}%2C{long}&start=latest&n_hrs=1&data_source=GFS&fcst_len=shortest&hr_inc=1&protocol=https%3A'

lat = 32.577899
long = 35.179972


# @app.route('/sounding_h_p.png', methods=['GET'])
# def sounding_p_t():
#     lat = flask.request.args.get('lat')
#     long = flask.request.args.get('long')
#
#     if lat is None or long is None:
#         raise exceptions.BadRequest('Must provide lat and long')
#
#     data = _get_data(lat, long)
#     plt = draw.plot_p_t(data)
#     return flask.send_file(plt, mimetype='image/png')
#
#
# @app.route('/sounding_h_t.png', methods=['GET'])
# def sounding_h_t():
#     lat = flask.request.args.get('lat')
#     long = flask.request.args.get('long')
#
#     if lat is None or long is None:
#         raise exceptions.BadRequest('Must provide lat and long')
#
#     data = _get_data(lat, long)
#     plt = draw.plot_h_t(data)
#     return flask.send_file(plt, mimetype='image/png')
#
#
# def _get_data(lat, long):
#     resp = requests.get(SOUNDING_URL.format(lat=lat, long=long))
#     if resp.status_code != 200:
#         raise exceptions.InternalServerError('Bad response from sounding server')
#
#     if len(resp.content) == 0:
#         raise exceptions.InternalServerError('Did not receive sounding data')
#
#     with open('/tmp/sounding.txt', 'w') as f:
#         f.write(resp.content)
#
#     return '/tmp/sounding.txt'
#
#
