import unittest
import json
from time import sleep

from kazoo.client import KazooClient
from kafka import KafkaConsumer

from scheduler import utils


# TODO add online test for run.py
class TestSendJobToKafka(unittest.TestCase):
    def setUp(self):
        # setup consumer
        self.topic = "test"
        self.consumer = KafkaConsumer(
            self.topic,
            bootstrap_servers='kafka:9092',
            group_id="jcss.test",
            auto_commit_interval_ms=10,
            consumer_timeout_ms=5000,
            auto_offset_reset='earliest',
            value_deserializer=lambda m: m.decode('utf-8')
        )
        sleep(1)

    def test_send_job_to_kafka(self):
        job = {
            "data": "test"
        }
        utils.send_job_to_kafka(self.topic, job)

        m = next(self.consumer)
        the_dict = json.loads(m.value)
        self.assertEquals(job, the_dict)

    def tearDown(self):
        # clean kafka test data
        for m in self.consumer:
            pass
        self.consumer.close()


class TestChangeSpiderConfig(unittest.TestCase):
    def setUp(self):
        # set up zookeeper connection
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
        # clean zookeeper test data
        self.zookeeper.delete(utils.zookeeper_file_path, recursive=True)
        self.zookeeper.stop()
        self.zookeeper.close()


if __name__ == '__main__':
    unittest.main()
