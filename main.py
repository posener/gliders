import logging
import sys
from datetime import datetime
from datetime import timedelta

import flask
from werkzeug import exceptions
from beaker import cache

import ims
import uwyo
import noaa
import calc
import plot
import stations
import timeformat


logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

app = flask.Flask(__name__)


DEFAULT_LOCATION = 'Megido'
# NOAA forecast data is for 5 days
# IMS forecast data is for 3 days
# We choose the minimum
FORECAST_HOURS = 3 * 24
FORECAST_RES_HOURS = 6

CACHE = cache.CacheManager()


@app.route('/', methods=['GET'])
def index():
    try:
        uwyo_table, data_time = uwyo.data()
    except uwyo.NoSoundingDataException:
        return flask.redirect('/no-data')

    locations = []
    max_tol = 0

    for loc in stations.all():
        station = stations.get(loc)
        loc = {
            'name': loc,
            'selected': False,
            'data': calc.calculate(uwyo_table, ims.temp_max(station), station['elevation']),
            'elevation': station['elevation'],
        }

        locations.append(loc)

        max_tol = max(max_tol, float(loc['data']['tol']))

    for loc in locations:
        loc['tol_percent'] = loc['data']['tol'] / max_tol * 100

    return flask.render_template(
        'index.html',
        location=None,
        hour=datetime.now().hour,
        locations=locations,
        data_time=timeformat.format(data_time),
    )


@app.route('/locations/<location_name>', methods=['GET'])
def site(location_name):
    _, data_time = uwyo.data()

    return flask.render_template(
        'location.html',
        location=location_name,
        hour=datetime.now().hour,
        locations=locations(location_name),
        data_time=data_time,
        forecast_dates=forecast_dates(),
    )


@app.route('/locations/<location_name>/<date>', methods=['GET'])
def forecast(location_name, date):
    try:
        date = timeformat.parse(date)
    except timeformat.InvalidDateFormatException:
        return flask.redirect('/?error=invalid-date-format')

    data_time = noaa.data_time(date)

    return flask.render_template(
        'forecast.html',
        location=location_name,
        locations=locations(location_name),
        data_time=timeformat.format(data_time),
        forecast_dates=forecast_dates(),
    )


@app.route('/sounding/<location_name>.png', methods=['GET'])
def sounding(location_name):
    location_name = location_name.split('-')[0]
    station = stations.get(location_name)
    uwyo_table, time = uwyo.data()
    temp = ims.temp_max(station)
    data = calc.calculate(uwyo_table, temp, station['elevation'])
    return flask.send_file(plot.plot(data), mimetype='image/png')


@app.route('/sounding/<location_name>/<date>.png', methods=['GET'])
def sounding_forecast(location_name, date):
    try:
        date = timeformat.parse(date)
    except timeformat.InvalidDateFormatException:
        return exceptions.BadRequest('Invalid date format')

    location_name = location_name.split('-')[0]
    station = stations.get(location_name)
    uwyo_table, time = noaa.data(date)

    try:
        temp = ims.temp_forecast(station, date)
    except ims.NoForecastForDateException:
        return flask.redirect('/static/confused.png')

    data = calc.calculate(uwyo_table, temp, station['elevation'])
    return flask.send_file(plot.plot(data), mimetype='image/png')


@app.route('/no-data', methods=['GET'])
def no_data():
    return flask.render_template(
        'no_data.html',
        hour=datetime.now().hour,
    )


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


def locations(location_name):
    return [
        {'name': loc, 'selected': loc == location_name}
        for loc in stations.all()
    ]


@CACHE.cache('forecast-dates', expire=3*60*60)
def forecast_dates():
    now = datetime.now()
    first_forecast_hour = now.hour-(now.hour % FORECAST_RES_HOURS) + FORECAST_RES_HOURS
    now = now.replace(hour=first_forecast_hour, minute=0, second=0, microsecond=0)
    return [
        timeformat.format(now + timedelta(hours=FORECAST_RES_HOURS*i))
        for i in range(FORECAST_HOURS / FORECAST_RES_HOURS)
    ]
