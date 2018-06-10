#! /usr/bin/env python
import requests
import logging
import sys

import yaml

import ims


logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


def main():
    stations = _stations()
    result = {}
    for st in stations:
        name = str(' '.join(part.capitalize() for part in st['name'].split()))
        if not st['active']:
            logging.info('Skipping - inactive: %s', name)
            continue
        if st['name'] not in _ALL_STATIONS:
            logging.info('Skipping - not important: %s', name)
            continue

        lat = st['location']['latitude']
        long = st['location']['longitude']
        if lat is None or long is None:
            logging.info('Skipping - no location: %s', name)
            continue

        elevation = _elevation(lat=lat, long=long)
        logging.info('%s: found elevation %f', name, elevation)

        logging.info('%s: adding to result')
        result[name] = {
            'id': st['stationId'],
            'elevation': elevation,
            'coord': {
                'lat': lat,
                'long': long,
            }
        }

    yaml.dump(result, open('new_stations.yaml', 'w'))


def _stations():
    resp = ims.session.get('https://api.ims.gov.il/v1/envista/stations')
    resp.raise_for_status()
    return resp.json()


def _elevation(lat, long):
    resp = requests.get(
        'https://api.open-elevation.com/api/v1/lookup?locations={lat},{long}'.format(lat=lat, long=long)
    )
    resp.raise_for_status()
    return resp.json()['results'][0]['elevation'] * 3.28084




_ALL_STATIONS = set([
    'AFULA NIR HAEMEQ',
    'ARAD',
    'AYYELET HASHAHAR',
    'BEER SHEVA',
    'BEER SHEVA UNI',
    'BEIT JIMAL',
    'BESOR FARM',
    'BET DAGAN',
    'BET DAGAN RAD',
    'BET HAARAVA',
    'BET ZAYDA',
    'DAFNA',
    'DEIR HANNA',
    'DOROT',
    'EDEN FARM',
    'ELAT',
    'ELON',
    'EN GEDI',
    'EN HAHORESH',
    'EN HASHOFET',
    'EN KARMEL',
    'ESHHAR',
    'EZUZ',
    'GALED',
    'GAMLA',
    'GAT',
    'GILGAL',
    'HADERA PORT',
    'HAFEZ HAYYIM',
    'HAIFA REFINERIES',
    'HAIFA TECHNION',
    'HAIFA UNIVERSITY',
    'HAKFAR HAYAROK',
    'HAR HARASHA',
    'HARASHIM',
    'HAZEVA',
    'ITAMAR',
    'JERUSALEM CENTRE',
    'JERUSALEM GIVAT RAM',
    'KEFAR BLUM',
    'KEFAR GILADI',
    'KEFAR NAHUM',
    'LAHAV',
    'LEV KINERET',
    'MAALE ADUMMIM',
    'MAALE GILBOA',
    'MASSADA',
    'MERHAVYA 20170702',
    'MEROM GOLAN PICMAN',
    'METZOKE DRAGOT',
    'MIZPE RAMON',
    'MIZPE RAMON 20120927',
    'NAHSHON',
    'NEGBA',
    'NEOT SMADAR',
    'NETIV HALAMED HE',
    'NEVATIM',
    'NEWE YAAR',
    'NIZZAN',
    'PARAN',
    'PARAN 20060124',
    'QARNE SHOMERON',
    'QEVUZAT YAVNE',
    'ROSH HANIQRA',
    'ROSH ZURIM',
    'SEDE BOQER',
    'SEDE BOQER UNI',
    'SEDE ELIYYAHU',
    'SEDOM',
    'SHAARE TIQWA 20161205',
    'SHANI',
    'SHAVE ZIYYON',
    'TAVOR KADOORIE',
    'TEL AVIV COAST',
    'YOTVATA',
    'ZEFAT HAR KENAAN',
    'ZIKHRON YAAQOV',
])

if __name__ == '__main__':

    main()
