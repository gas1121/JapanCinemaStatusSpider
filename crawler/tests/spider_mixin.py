import sys
import json
from mock import patch
from time import sleep
import threading

from twisted.internet import reactor
from scrapy.crawler import CrawlerRunner

import arrow
import redis
from kazoo.client import KazooClient
from kafka import KafkaConsumer
from scrapy.utils.project import get_project_settings


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
        self.patcher = patch(
            'crawler.utils.spider_helper.get_project_settings')
        self.mock_get_project_settings = self.patcher.start()
        self.mock_get_project_settings.return_value = self.settings

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
        config_path = self.jcss_zookeeper_path + "test-spider"
        self.zookeeper.ensure_path(config_path)
        # set spider config
        spider_config = {}
        spider_config['use_sample'] = False
        spider_config['crawl_booking_data'] = True
        spider_config['use_proxy'] = False
        spider_config['require_js'] = False
        spider_config['crawl_all_cinemas'] = True
        spider_config['crawl_all_movies'] = True
        spider_config['movie_list'] = []
        spider_config['cinema_list'] = []
        spider_config['date'] = arrow.now(
            'UTC+9').shift(days=+1).format('YYYYMMDD')
        self.zookeeper.set(config_path, json.dumps(
            spider_config).encode('utf-8'))

    def tearDown(self):
        # clear out older test keys if any
        keys = self.redis_conn.keys('stats:crawler:*:test-spider:*')
        keys = keys + self.redis_conn.keys('*test-spider:*')
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

        self.patcher.stop()


class BaseSpiderRunCase(SpiderMixin):
    def setUp(self, url, spider_cls, wait_time=20):
        SpiderMixin.setUp(self)

        feed_data = {
            'allowed_domains': None,
            'allow_regex': None,
            'crawlid': 'abc12345',
            'url': url,
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
        self.spider_cls = spider_cls
        self.wait_time = wait_time

    def test_crawler_process(self):
        runner = CrawlerRunner(self.settings)
        # pass settings as parameter
        d = runner.crawl(self.spider_cls)
        d.addBoth(lambda _: reactor.stop())

        # add crawl to redis
        key = "test-spider:tohotheater.jp:queue"
        self.redis_conn.zadd(key, self.example_feed, -99)

        # run the spider, give 20 seconds to crawl. Then we kill the reactor
        def thread_func():
            sleep(self.wait_time)
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
            if self.is_message_count(the_dict):
                    message_count += 1

        self.assertGreaterEqual(message_count, 1)

    def tearDown(self):
        SpiderMixin.tearDown(self)
