import unittest
import json

import arrow

from crawler.showingspiders.cinemasunshine import CinemaSunshineSpider
from .spider_mixin import BaseSpiderRunCase


class CustomSpider(CinemaSunshineSpider):
    '''
    Overridden spider name for testing
    '''
    name = "test-spider"


class TestSpider(unittest.TestCase, BaseSpiderRunCase):
    def setUp(self):
        BaseSpiderRunCase.setUp(
            self, 'http://www.cinemasunshine.co.jp/theater/', CustomSpider,
            100)
        # over settings to test cinemasunshine's new cinema
        # set spider config
        spider_config = {}
        spider_config['use_sample'] = False
        spider_config['crawl_booking_data'] = True
        spider_config['use_proxy'] = False
        spider_config['require_js'] = False
        spider_config['crawl_all_cinemas'] = False
        spider_config['crawl_all_movies'] = True
        spider_config['movie_list'] = []
        spider_config['cinema_list'] = ['シネマサンシャイン姶良']
        spider_config['date'] = arrow.now(
            'UTC+9').shift(days=+1).format('YYYYMMDD')
        config_path = self.jcss_zookeeper_path + "test-spider"
        self.zookeeper.set(config_path, json.dumps(
            spider_config).encode('utf-8'))

    def is_message_count(self, the_dict):
        # item is Showing or ShowingBooking
        if the_dict:
            if ('showing' not in the_dict and 'title' in the_dict
                    and the_dict['title'] and 'seat_type' in the_dict
                    and the_dict['seat_type']):
                return True
            elif ('showing' in the_dict and 'book_status' in the_dict
                    and the_dict['book_status']):
                return True
        return False

    def tearDown(self):
        BaseSpiderRunCase.tearDown(self)


if __name__ == '__main__':
    unittest.main()
