import sys
import json
from time import sleep

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
