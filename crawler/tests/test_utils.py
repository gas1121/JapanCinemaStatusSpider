import json
import unittest
from mock import MagicMock

from crawler.utils import standardize_county_name, ScrapyClusterSpider


class TestSiteUtils(unittest.TestCase):
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


class BasicScrapyClusterSpider(ScrapyClusterSpider):
    def __init__(self):
        pass


class TestScrapyClusterSpider(unittest.TestCase):
    def setUp(self):
        self.spider = BasicScrapyClusterSpider()
        self.spider._logger = MagicMock()

    def test_change_config(self):
        self.spider.error_config = MagicMock()
        config_string = ""
        self.spider.change_config(config_string)
        self.spider.error_config.assert_called_once()

        self.spider.loaded_config = {}
        d = {
            "use_sample": False
        }
        config_string = json.dumps(d)
        self.spider.change_config(config_string)
        self.assertEqual(self.spider.loaded_config['use_sample'], False)

    def test_error_config(self):
        self.spider.error_config("")
        self.assertEqual(self.spider.loaded_config['date'], '20170101')

    def test_set_next_func(self):
        def func1():
            pass
        request = MagicMock()
        request.meta = {}
        self.spider.set_next_func(request, func1)
        self.assertEqual(request.meta["curr_step"], func1.__name__)
        pass
