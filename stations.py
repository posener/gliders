import yaml
from werkzeug import exceptions


_STATIONS = yaml.load(open('stations.yaml'))


def get(name):
    try:
        station = _STATIONS[name]
    except KeyError:
        raise exceptions.NotFound('Station not found: {}'.format(station))

    return station


def all():
    return sorted(_STATIONS.keys())



