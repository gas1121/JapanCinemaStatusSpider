import json
import unittest
from mock import MagicMock, patch
from time import sleep

import redis
from kazoo.client import KazooClient
from scrapy.utils.project import get_project_settings
from scrapy.http import HtmlResponse
from scrapy.http import Request

from crawler.utils import ScrapyClusterSpider
from crawler.middlewares.cookies import RedisCookiesMiddleware


class BasicScrapyClusterSpider(ScrapyClusterSpider):
    name = "basic"

    def __init__(self):
        super().__init__()

    def parse_next(self, response, result_list):
        result_list.append("test")


class TestScrapyClusterSpider(unittest.TestCase):
    def setUp(self):
        zookeeper_host = "zookeeper:2181"
        self.zookeeper_path = "/test/"
        settings = get_project_settings()
        settings.set('IP_ADDR_REGEX', '.*')
        settings.set('PUBLIC_IP_URL', 'http://ip.42.pl/raw')
        settings.set('ZOOKEEPER_HOSTS', zookeeper_host)
        settings.set('JCSS_ZOOKEEPER_PATH', self.zookeeper_path)
        self.patcher = patch(
            'crawler.utils.spider_helper.get_project_settings')
        self.mock_get_project_settings = self.patcher.start()
        self.mock_get_project_settings.return_value = settings

        self.zookeeper = KazooClient(hosts=zookeeper_host)
        self.zookeeper.start()

        self.spider = BasicScrapyClusterSpider()
        self.spider._logger = MagicMock()
        self.spider_path = self.zookeeper_path + self.spider.name

    def test_change_config(self):
        d = {"a": 1}
        data = json.dumps(d)
        self.zookeeper.set(self.spider_path, data.encode('utf-8'))
        # sleep some time to make sure callback is called
        sleep(1)
        self.assertEqual(self.spider.loaded_config, d)

    def test_error_config(self):
        d = {"a": 1}
        data = json.dumps(d)
        self.zookeeper.set(self.spider_path, data.encode('utf-8'))
        sleep(1)
        self.zookeeper.set(self.spider_path, "".encode('utf-8'))
        sleep(1)
        self.assertEqual(self.spider.loaded_config['date'], '20170101')

    def tearDown(self):
        self.spider.zoo_watcher.close()
        # clean zookeeper test data
        self.zookeeper.delete(self.zookeeper_path, recursive=True)
        self.zookeeper.stop()
        self.zookeeper.close()

        self.patcher.stop()


class TestRedisCookiesMiddleware(unittest.TestCase):
    def setUp(self):
        settings = get_project_settings()
        settings.set('REDIS_HOST', 'redis')
        settings.set('REDIS_PORT', 6379)
        settings.set('REDIS_DB', 0)
        settings.set('COOKIES_ENABLED', True)
        settings.set('COOKIES_DEBUG', False)
        crawler = MagicMock()
        crawler.settings = settings
        self.middleware = RedisCookiesMiddleware.from_crawler(crawler)

        self.redis_conn = redis.Redis(host=settings['REDIS_HOST'],
                                      port=settings['REDIS_PORT'],
                                      db=settings['REDIS_DB'],
                                      decode_responses=True)

    def test_process_request(self):
        meta = {
            'dont_merge_cookies': False,
            'cookiejar': None,

        }
        name = 'test'
        uuid = 'uuid'
        key = "cookie:{}:{}:{}".format(name, uuid, 'all')
        self.assertFalse(self.redis_conn.exists(key))
        request = Request(url='http://www.baidu.com', meta=meta)
        spider = MagicMock()
        spider.name = name
        spider.uuid = uuid
        self.middleware.process_request(request, spider)
        self.assertTrue(self.redis_conn.exists(key))
        data = self.redis_conn.get(key)
        jar_dict = json.loads(data)
        self.assertFalse(jar_dict)

        origin_dict = {'a': 'b'}
        self.redis_conn.set(key, json.dumps(origin_dict))
        request = Request(url='http://www.baidu.com', meta=meta,
                          cookies={'key': 'value'})
        self.middleware.process_request(request, spider)
        self.assertTrue(self.redis_conn.exists(key))
        data = self.redis_conn.get(key)
        jar_dict = json.loads(data)
        self.assertEqual(jar_dict['a'], 'b')
        self.assertEqual(jar_dict['key'], 'value')

    def test_process_response(self):
        meta = {
            'dont_merge_cookies': False,
            'cookiejar': None,

        }
        name = 'test'
        uuid = 'uuid'
        key = "cookie:{}:{}:{}".format(name, uuid, 'all')
        self.assertFalse(self.redis_conn.exists(key))
        request = Request(url='http://www.baidu.com', meta=meta)
        response = HtmlResponse(url='http://www.baidu.com', headers={
            'Set-Cookie': 'key=value'})
        spider = MagicMock()
        spider.name = name
        spider.uuid = uuid
        self.middleware.process_response(request, response, spider)
        self.assertTrue(self.redis_conn.exists(key))
        data = self.redis_conn.get(key)
        jar_dict = json.loads(data)
        self.assertEqual(jar_dict['key'], 'value')

    def tearDown(self):
        # delete test keys
        keys = self.redis_conn.keys('*test*')
        for key in keys:
            self.redis_conn.delete(key)


if __name__ == '__main__':
    unittest.main()
