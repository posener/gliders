import unittest
from datetime import datetime
from datetime import timedelta

import noaa
import uwyo
import ims


class TestFetch(unittest.TestCase):

    def test_noaa(self):
        d = noaa.data(datetime.now())
        self._test_data(d[0])

    def test_uwyo(self):
        d = uwyo.data()
        self._test_data(d[0])

    def _test_data(self, data):
        MIN_LEN = 5
        self.assertGreater(len(data.T), MIN_LEN)
        self.assertGreater(len(data.Td), MIN_LEN)
        self.assertGreater(len(data.h), MIN_LEN)
        self.assertGreater(len(data.p), MIN_LEN)
        self.assertGreater(len(data.wind_u), MIN_LEN)
        self.assertGreater(len(data.wind_v), MIN_LEN)

    def test_temp_max(self):
        data = ims.temp_max({'temp_max_id': '513'})
        self.assertIsNotNone(data)

    def test_temp_forecast(self):
        now = datetime.now()
        temp = ims.temp_forecast({'temp_max_id': '513'}, now)
        self.assertIsNotNone(temp)

        tomorrow = now + timedelta(days=1)
        temp = ims.temp_forecast({'temp_max_id': '513'}, tomorrow)
        self.assertIsNotNone(temp)

        in_two_days = now + timedelta(days=2)
        temp = ims.temp_forecast({'temp_max_id': '513'}, in_two_days)
        self.assertIsNotNone(temp)

        in_three_days = now + timedelta(days=3)
        temp = ims.temp_forecast({'temp_max_id': '513'}, in_three_days)
        self.assertIsNotNone(temp)

        with self.assertRaises(ims.NoForecastForDateException):
            in_four_days = now + timedelta(days=4)
            ims.temp_forecast({'temp_max_id': '513'}, in_four_days)
