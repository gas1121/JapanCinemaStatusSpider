import json
import unittest
from time import sleep
import threading

from twisted.internet import reactor
from scrapy.crawler import CrawlerRunner

from crawler.moviespiders.walkerplus_movie import WalkerplusMovieSpider
from .spider_mixin import BaseSpiderRunCase


class CustomSpider(WalkerplusMovieSpider):
    '''
    Overridden spider name for testing
    '''
    name = "test-spider"


class TestSpider(unittest.TestCase, BaseSpiderRunCase):
    def setUp(self):
        BaseSpiderRunCase.setUp(
            self, 'http://movie.walkerplus.com/list/', CustomSpider)

    def is_message_count(self, the_dict):
        if the_dict is not None and 'title' in the_dict \
                and the_dict['title'] \
                and 'current_cinema_count' in the_dict:
            return True
        return False

    def tearDown(self):
        BaseSpiderRunCase.tearDown(self)


if __name__ == '__main__':
    unittest.main()
