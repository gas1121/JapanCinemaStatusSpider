import json
import unittest
from mock import MagicMock
from time import sleep
import threading

from kazoo.client import KazooClient
from twisted.internet import reactor
from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings

from crawler.utils import ScrapyClusterSpider
from crawler.moviespiders.walkerplus_movie import WalkerplusMovieSpider


class BasicScrapyClusterSpider(ScrapyClusterSpider):
    name = "basic"

    def __init__(self):
        super().__init__(
            zookeeper_hosts="zookeeper:2181", jcss_zookeeper_path="/test/")

    def parse_next(self, response, result_list):
        result_list.append("test")


class TestScrapyClusterSpider(unittest.TestCase):
    def setUp(self):
        zookeeper_host = "zookeeper:2181"
        self.zookeeper_path = "/test/"
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


class CustomWalkerplusMovieSpider(WalkerplusMovieSpider):
    '''
    Overridden spider name for testing
    '''
    name = "test-spider"


class TestWalkerplusMovieSpider(unittest.TestCase):
    def setUp(self):
        self.settings = get_project_settings()
        self.settings.set('JCSS_DATA_PROCESSOR_TOPIC', "jcss.test")
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

        self.zookeeper_host = self.settings.get('ZOOKEEPER_HOSTS')
        self.jcss_zookeeper_path = self.settings.get('JCSS_ZOOKEEPER_PATH')
        self.zookeeper = KazooClient(hosts=self.zookeeper_host)
        self.zookeeper.start()
        self.zookeeper.ensure_path(self.settings.get('ZOOKEEPER_ASSIGN_PATH'))
        self.zookeeper.ensure_path(self.jcss_zookeeper_path)

    def test_crawler_process(self):
        runner = CrawlerRunner(self.settings)
        # pass settings as parameter
        d = runner.crawl(
            CustomWalkerplusMovieSpider, zookeeper_hosts=self.zookeeper_host,
            jcss_zookeeper_path=self.jcss_zookeeper_path)
        d.addBoth(lambda _: reactor.stop())

        # run the spider, give 20 seconds to crawl. Then we kill the reactor
        def thread_func():
            sleep(5)
            reactor.stop()

        # TODO finish test case

        thread = threading.Thread(target=thread_func)
        thread.start()
        reactor.run()

    def tearDown(self):
        # clean zookeeper test data
        self.zookeeper.delete(
            self.settings.get('JCSS_ZOOKEEPER_PATH'), recursive=True)
        self.zookeeper.delete(
            self.settings.get('ZOOKEEPER_ASSIGN_PATH'), recursive=True)
        self.zookeeper.stop()
        self.zookeeper.close()


if __name__ == '__main__':
    unittest.main()
