import unittest
from datetime import datetime

import timeformat


class TestTimeformat(unittest.TestCase):

    def test_timeformat(self):
        self.assertEqual(timeformat.parse('13-08-2018H09:00'), datetime(year=2018, month=8, day=13, hour=9))

    def test_bad_format(self):
        with self.assertRaises(timeformat.InvalidDateFormatException):
            timeformat.parse('13-8-2018-9:00')
