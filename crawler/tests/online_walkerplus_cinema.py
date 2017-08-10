import sys
import json
import unittest
from time import sleep
import threading

import redis
from kazoo.client import KazooClient
from kafka import KafkaConsumer
from twisted.internet import reactor
from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings

from crawler.cinemaspiders.walkerplus_cinema import WalkerplusCinemaSpider


class SpiderMixin(object):
    def setUp(self):
        # setting
        self.topic = "jcss.test"
        self.settings = get_project_settings()
        self.settings.set('JCSS_DATA_PROCESSOR_TOPIC', self.topic)
        self.settings.set('JCSS_ZOOKEEPER_PATH', "/test/")
        self.settings.set('SC_LOG_STDOUT', True)
        self.settings.set('ZOOKEEPER_ASSIGN_PATH', '/demo_test/')
        self.settings.set('KAFKA_TOPIC_PREFIX', "demo_test")
        self.settings.set('LOG_FILE', None)
        # add debug middleware
        spider_middlewares = self.settings.getdict('SPIDER_MIDDLEWARES')
        spider_middlewares[
            'crawler.spidermiddlewares.debug_single_output.'
            'DebugSingleOutputMiddleware'] = 999
        self.settings.set('SPIDER_MIDDLEWARES', spider_middlewares)

        # set up redis
        self.redis_conn = redis.Redis(host=self.settings['REDIS_HOST'],
                                      port=self.settings['REDIS_PORT'],
                                      db=self.settings['REDIS_DB'],
                                      decode_responses=True)
        try:
            self.redis_conn.info()
        except ConnectionError:
            print("Could not connect to Redis")
            # plugin is essential to functionality
            sys.exit(1)

        # set up kafka to consumer potential result
        self.consumer = KafkaConsumer(
            self.topic,
            bootstrap_servers=self.settings['KAFKA_HOSTS'],
            group_id="demo-id",
            auto_commit_interval_ms=10,
            consumer_timeout_ms=5000,
            auto_offset_reset='earliest',
            value_deserializer=lambda m: m.decode('utf-8')
        )
        sleep(2)

        # set up zookeeper
        self.zookeeper_host = self.settings.get('ZOOKEEPER_HOSTS')
        self.jcss_zookeeper_path = self.settings.get('JCSS_ZOOKEEPER_PATH')
        self.zookeeper = KazooClient(hosts=self.zookeeper_host)
        self.zookeeper.start()
        self.zookeeper.ensure_path(self.settings.get('ZOOKEEPER_ASSIGN_PATH'))
        self.zookeeper.ensure_path(self.jcss_zookeeper_path)

    def tearDown(self):
        # clear out older test keys if any
        keys = self.redis_conn.keys('stats:crawler:*:test-spider:*')
        keys = keys + self.redis_conn.keys('test-spider:*')
        for key in keys:
            self.redis_conn.delete(key)

        # clean zookeeper test data
        self.zookeeper.delete(self.jcss_zookeeper_path, recursive=True)
        self.zookeeper.delete(
            self.settings.get('ZOOKEEPER_ASSIGN_PATH'), recursive=True)
        self.zookeeper.stop()
        self.zookeeper.close()

        # make sure no test kafka message is left
        for m in self.consumer:
            pass
        self.consumer.close()


class CustomWalkerplusCinemaSpider(WalkerplusCinemaSpider):
    '''
    Overridden spider name for testing
    '''
    name = "test-spider"


class TestWalkerplusCinemaSpider(unittest.TestCase, SpiderMixin):
    def setUp(self):
        SpiderMixin.setUp(self)

        feed_data = {
            'allowed_domains': None,
            'allow_regex': None,
            'crawlid': 'abc12345',
            'url': 'http://movie.walkerplus.com/theater/',
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
            CustomWalkerplusCinemaSpider,
            zookeeper_hosts=self.zookeeper_host,
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
            if the_dict is not None and 'county' in the_dict \
                    and 'screen_count' in the_dict:
                message_count += 1

        self.assertGreaterEqual(message_count, 1)

    def tearDown(self):
        SpiderMixin.tearDown(self)


if __name__ == '__main__':
    unittest.main()
