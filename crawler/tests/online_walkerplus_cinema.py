import unittest

from crawler.cinemaspiders.walkerplus_cinema import WalkerplusCinemaSpider
from .spider_mixin import BaseSpiderRunCase


class CustomSpider(WalkerplusCinemaSpider):
    '''
    Overridden spider name for testing
    '''
    name = "test-spider"


class TestSpider(unittest.TestCase, BaseSpiderRunCase):
    def setUp(self):
        BaseSpiderRunCase.setUp(
            self, 'http://movie.walkerplus.com/theater/', CustomSpider)

    def is_message_count(self, the_dict):
        if the_dict is not None and 'county' in the_dict \
                and the_dict['county'] \
                and 'screen_count' in the_dict \
                and the_dict['screen_count'] > 0:
            return True
        return False

    def tearDown(self):
        BaseSpiderRunCase.tearDown(self)


if __name__ == '__main__':
    unittest.main()
