import unittest
import json
from kazoo.client import KazooClient

import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from scheduler import utils


class TestChangeSpiderConfig(unittest.TestCase):
    def setUp(self):
        utils.zookeeper_file_path = "/test/"
        utils.zookeeper_file_id = "all"
        self.full_path = utils.zookeeper_file_path + utils.zookeeper_file_id
        self.zookeeper = KazooClient(hosts=utils.zookeeper_host)
        self.zookeeper.start()

    def test_change_spider_config(self):
        self.assertFalse(self.zookeeper.exists(utils.zookeeper_file_path))
        utils.change_spider_config()
        self.assertTrue(self.zookeeper.exists(self.full_path))
        data = self.zookeeper.get(self.full_path)[0]
        d = json.loads(data.decode('utf-8'))
        self.assertEqual(d["use_sample"], False)
        self.assertEqual(d["crawl_booking_data"], False)

        utils.change_spider_config(use_sample=True, crawl_booking_data=True)
        data = self.zookeeper.get(self.full_path)[0]
        d = json.loads(data.decode('utf-8'))
        self.assertEqual(d["use_sample"], True)
        self.assertEqual(d["crawl_booking_data"], True)

    def tearDown(self):
        # clean test data
        self.zookeeper.delete(utils.zookeeper_file_path, recursive=True)
        self.zookeeper.stop()
        self.zookeeper.close()


if __name__ == '__main__':
    unittest.main()
