import unittest
import json
from time import sleep

from kazoo.client import KazooClient
from kafka import KafkaConsumer

from scheduler import utils


class TestChangeSpiderConfig(unittest.TestCase):
    def test_send_job_to_kafka(self):
        # setup consumer
        topic = "test"
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers='kafka:9092',
            group_id="jcss.test",
            auto_commit_interval_ms=10,
            consumer_timeout_ms=5000,
            auto_offset_reset='earliest',
            value_deserializer=lambda m: m.decode('utf-8')
        )
        sleep(1)

        job = {
            "data": "test"
        }
        utils.send_job_to_kafka(topic, job)

        m = next(consumer)
        the_dict = json.loads(m.value)
        self.assertEquals(job, the_dict)

        # clean kafka test data
        for m in consumer:
            pass
        consumer.close()

    def test_change_spider_config(self):
        # set up zookeeper connection
        utils.zookeeper_file_path = "/test/"
        utils.zookeeper_file_id = "all"
        full_path = utils.zookeeper_file_path + utils.zookeeper_file_id
        zookeeper = KazooClient(hosts=utils.zookeeper_host)
        zookeeper.start()

        self.assertFalse(zookeeper.exists(utils.zookeeper_file_path))
        utils.change_spider_config()
        self.assertTrue(zookeeper.exists(full_path))
        data = zookeeper.get(full_path)[0]
        d = json.loads(data.decode('utf-8'))
        self.assertEqual(d["use_sample"], False)
        self.assertEqual(d["crawl_booking_data"], False)

        utils.change_spider_config(use_sample=True, crawl_booking_data=True)
        data = zookeeper.get(full_path)[0]
        d = json.loads(data.decode('utf-8'))
        self.assertEqual(d["use_sample"], True)
        self.assertEqual(d["crawl_booking_data"], True)

        # clean zookeeper test data
        zookeeper.delete(utils.zookeeper_file_path, recursive=True)
        zookeeper.stop()
        zookeeper.close()


if __name__ == '__main__':
    unittest.main()
