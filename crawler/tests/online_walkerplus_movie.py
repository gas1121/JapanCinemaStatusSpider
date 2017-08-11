import json
import unittest
from time import sleep
import threading

from twisted.internet import reactor
from scrapy.crawler import CrawlerRunner

from crawler.moviespiders.walkerplus_movie import WalkerplusMovieSpider
from .spider_mixin import SpiderMixin


class CustomWalkerplusMovieSpider(WalkerplusMovieSpider):
    '''
    Overridden spider name for testing
    '''
    name = "test-spider"


class TestWalkerplusMovieSpider(unittest.TestCase, SpiderMixin):
    def setUp(self):
        SpiderMixin.setUp(self)

        feed_data = {
            'allowed_domains': None,
            'allow_regex': None,
            'crawlid': 'abc12345',
            'url': 'http://movie.walkerplus.com/list/',
            'expires': 0,
            'ts': 1461549923.7956631184,
            'priority': 1,
            'deny_regex': None,
            'cookie': None,
            'attrs': None,
            'appid': 'test',
            'spiderid': 'test-spider',
            'useragent': None,
            'deny_extensions': None,
            'maxdepth': 0,
        }
        self.example_feed = json.dumps(feed_data)

    def test_crawler_process(self):
        runner = CrawlerRunner(self.settings)
        # pass settings as parameter
        d = runner.crawl(
            CustomWalkerplusMovieSpider, zookeeper_hosts=self.zookeeper_host,
            jcss_zookeeper_path=self.jcss_zookeeper_path)
        d.addBoth(lambda _: reactor.stop())

        # add crawl to redis
        key = "test-spider:walkerplus.com:queue"
        self.redis_conn.zadd(key, self.example_feed, -99)

        # run the spider, give 20 seconds to crawl. Then we kill the reactor
        def thread_func():
            sleep(20)
            runner.stop()

        thread = threading.Thread(target=thread_func)
        thread.start()
        reactor.run()

        message_count = 0
        m = next(self.consumer)

        if m is None:
            pass
        else:
            the_dict = json.loads(m.value)
            if the_dict is not None and 'title' in the_dict \
                    and the_dict['title'] \
                    and 'current_cinema_count' in the_dict:
                message_count += 1

        self.assertGreaterEqual(message_count, 1)

    def tearDown(self):
        SpiderMixin.tearDown(self)


if __name__ == '__main__':
    unittest.main()
