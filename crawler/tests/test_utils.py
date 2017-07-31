import unittest

from crawler.utils import standardize_county_name


class TestCreateCrawlJob(unittest.TestCase):
    def test_standardize_county_name(self):
        for name in ["東京都23区内", "東京都下", "東京", "東京都"]:
            self.assertEqual("東京都", standardize_county_name(name))
        self.assertEqual("大阪府", standardize_county_name("大阪"))
        self.assertEqual("大阪府", standardize_county_name("大阪府"))
        self.assertEqual("京都府", standardize_county_name("京都"))
        self.assertEqual("京都府", standardize_county_name("京都府"))
        self.assertEqual("北海道", standardize_county_name("北海道"))
        self.assertEqual("愛知県", standardize_county_name("愛知県"))
        self.assertEqual("愛知県", standardize_county_name("愛知"))
