import json
import unittest
from mock import MagicMock

from kazoo.client import KazooClient

from crawler.utils import ScrapyClusterSpider


class BasicScrapyClusterSpider(ScrapyClusterSpider):
    name = "basic"

    def __init__(self):
        self.settings = {
            "ZOOKEEPER_HOSTS": "zookeeper:2181",
            "JCSS_ZOOKEEPER_PATH": "/test/",
        }
        super().__init__()


class TestScrapyClusterSpider(unittest.TestCase):
    def setUp(self):
        zookeeper_host = "zookeeper:2181"
        self.zookeeper_path = "/test/"
        self.zookeeper = KazooClient(hosts=zookeeper_host)
        self.zookeeper.start()

        self.spider = BasicScrapyClusterSpider()
        self.spider._logger = MagicMock()

    def test_change_config(self):
        # TODO
        pass

    def test_error_config(self):
        # TODO
        pass

    def test_parse(self):
        # TODO
        pass

    def tearDown(self):
        self.spider.zoo_watcher.close()
        # clean zookeeper test data
        self.zookeeper.delete(self.zookeeper_path, recursive=True)
        self.zookeeper.stop()
        self.zookeeper.close()


if __name__ == '__main__':
    unittest.main()
