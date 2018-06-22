import logging
import sys
from datetime import datetime

import flask

import israel
import stations
import ims


logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

app = flask.Flask(__name__)


DEFAULT_LOCATION = 'Megido'


@app.route('/', methods=['GET'])
def index():
    station_name = flask.request.args.get('location', DEFAULT_LOCATION)

    station = stations.get(station_name)

    locations = [
        {'name': loc, 'selected': loc == station_name}
        for loc in stations.all()
    ]

    return flask.render_template(
        'index.html',
        location=station_name,
        locations=locations,
    )


@app.route('/sounding/<station_name>.png', methods=['GET'])
def sounding(station_name):
    station = stations.get(station_name)
    return flask.send_file(israel.get(station=station), mimetype='image/png')


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
