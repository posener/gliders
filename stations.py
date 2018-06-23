import yaml
from werkzeug import exceptions


_KEYS = {
    'coord',
    'elevation',
    'temp_max_id',
}

_STATIONS = {
    name: val
    for name, val in yaml.load(open('stations.yaml')).items()
    if set(val.keys()) >= _KEYS
}

_ALL = sorted(_STATIONS.keys())


def get(name):
    try:
        station = _STATIONS[name]
    except KeyError:
        raise exceptions.NotFound('Station not found: {}'.format(name))

    return station


def all():
    return _ALL
