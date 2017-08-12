import json
import unittest
from mock import MagicMock, patch
from time import sleep

import requests
from kazoo.client import KazooClient
from scrapy.utils.project import get_project_settings

from crawler.utils import ScrapyClusterSpider


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

    def test_update_ipaddress(self):
        r = requests.get('http://ip.42.pl/raw')
        self.assertEqual(self.spider.my_ip, r.text)

    def tearDown(self):
        self.spider.zoo_watcher.close()
        # clean zookeeper test data
        self.zookeeper.delete(self.zookeeper_path, recursive=True)
        self.zookeeper.stop()
        self.zookeeper.close()

        self.patcher.stop()


if __name__ == '__main__':
    unittest.main()
