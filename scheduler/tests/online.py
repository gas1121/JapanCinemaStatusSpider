import unittest
from mock import MagicMock
import json
from time import sleep

from kazoo.client import KazooClient
from kafka import KafkaConsumer

from run import (spider_setting, cinema_crawl_job, movie_crawl_job,
                 showing_crawl_job, showing_booking_crawl_job,
                 showing_booking_sample_crawl_job, set_throttle_job)
from scheduler.utils import send_job_to_kafka, change_spider_config


class TestRun(unittest.TestCase):
    def setUp(self):
        self.settings = {
            'KAFKA_HOSTS': 'kafka:9092',
            'JCSS_DATA_PROCESSOR_TOPIC': 'jcss.test',
            'KAFKA_INCOMING_TOPIC': 'demo.test',
            'JCSS_ZOOKEEPER_HOST': 'zookeeper:2181',
            'JCSS_ZOOKEEPER_PATH': '/test/',
            'JCSS_DEFAULT_MOVIES': ['movie1'],
            'JCSS_SAMPLE_CINEMAS': ['sample_cinema1'],
            'JCSS_DEFAULT_CINEMAS': {
                "aeon": ['cinema1'],
                "toho_v2": ['cinema1'],
                "united": ['cinema1'],
                "movix": ['cinema1'],
                "kinezo": ['cinema1'],
                "cinema109": ['cinema1'],
                "korona": ['cinema1'],
                "cinemasunshine": ['cinema1'],
                "forum": ['cinema1'],
            },
        }
        self.logger = MagicMock()

        # set up kafka to consumer potential result
        self.jcss_consumer = KafkaConsumer(
            self.settings['JCSS_DATA_PROCESSOR_TOPIC'],
            bootstrap_servers=self.settings['KAFKA_HOSTS'],
            group_id="jcss-test",
            auto_commit_interval_ms=10,
            consumer_timeout_ms=5000,
            auto_offset_reset='earliest',
            value_deserializer=lambda m: m.decode('utf-8')
        )
        sleep(2)
        self.consumer = KafkaConsumer(
            self.settings['KAFKA_INCOMING_TOPIC'],
            bootstrap_servers=self.settings['KAFKA_HOSTS'],
            group_id="test",
            auto_commit_interval_ms=10,
            consumer_timeout_ms=5000,
            auto_offset_reset='earliest',
            value_deserializer=lambda m: m.decode('utf-8')
        )
        sleep(2)

        # zookeeper client
        self.zookeeper_path = self.settings['JCSS_ZOOKEEPER_PATH']
        self.zookeeper = KazooClient(
            hosts=self.settings['JCSS_ZOOKEEPER_HOST'])
        self.zookeeper.start()

    def test_cinema_crawl_job(self):
        cinema_crawl_job(self.logger, self.settings)
        jcss_message_count = 0
        for m in self.jcss_consumer:
            if m is None:
                pass
            the_dict = json.loads(m.value)
            if the_dict is not None and 'action' in the_dict \
                    and the_dict['action'] \
                    and 'target' in the_dict \
                    and the_dict['target'] == 'cinema':
                jcss_message_count += 1

        self.assertEqual(jcss_message_count, 1)

        message_count = 0
        for m in self.consumer:
            if m is None:
                pass
            the_dict = json.loads(m.value)
            if the_dict is not None and 'url' in the_dict \
                    and the_dict['url'] \
                    and 'spiderid' in the_dict \
                    and the_dict['spiderid'] == 'walkerplus_cinema':
                message_count += 1

        self.assertEqual(message_count, 1)

    def test_movie_crawl_job(self):
        movie_crawl_job(self.logger, self.settings)
        jcss_message_count = 0
        for m in self.jcss_consumer:
            if m is None:
                pass
            the_dict = json.loads(m.value)
            if the_dict is not None and 'action' in the_dict \
                    and the_dict['action'] \
                    and 'target' in the_dict \
                    and the_dict['target'] == 'movie':
                jcss_message_count += 1

        self.assertEqual(jcss_message_count, 1)

        message_count = 0
        for m in self.consumer:
            if m is None:
                pass
            the_dict = json.loads(m.value)
            if the_dict is not None and 'url' in the_dict \
                    and the_dict['url'] \
                    and 'spiderid' in the_dict \
                    and the_dict['spiderid'] == 'walkerplus_movie':
                message_count += 1

        self.assertEqual(message_count, 1)

    def test_showing_crawl_job(self):
        showing_crawl_job(self.logger, self.settings)

        for spider_id in spider_setting:
            path = self.zookeeper_path + spider_id
            data = self.zookeeper.get(path)[0]
            data_dict = json.loads(data.decode('utf-8'))
            self.assertEqual(data_dict['use_sample'], False)
            self.assertEqual(data_dict['crawl_booking_data'], False)
            self.assertEqual(data_dict['crawl_all_cinemas'], True)
            self.assertEqual(data_dict['crawl_all_movies'], True)

        message_count = 0
        for m in self.consumer:
            if m is None:
                pass
            the_dict = json.loads(m.value)
            if the_dict is not None and 'url' in the_dict \
                    and the_dict['url'] \
                    and 'spiderid' in the_dict \
                    and the_dict['spiderid'] == 'walkerplus_movie':
                message_count += 1

        self.assertEqual(message_count, 1)

    def test_showing_booking_crawl_job(self):
        showing_booking_crawl_job(self.logger, self.settings)

        for spider_id in spider_setting:
            path = self.zookeeper_path + spider_id
            data = self.zookeeper.get(path)[0]
            data_dict = json.loads(data.decode('utf-8'))
            self.assertEqual(data_dict['use_sample'], False)
            self.assertEqual(data_dict['crawl_booking_data'], True)
            self.assertEqual(data_dict['crawl_all_cinemas'], True)
            self.assertEqual(data_dict['crawl_all_movies'], True)

        message_count = 0
        for m in self.consumer:
            if m is None:
                pass
            the_dict = json.loads(m.value)
            if the_dict is not None and 'url' in the_dict \
                    and the_dict['url'] \
                    and 'spiderid' in the_dict \
                    and the_dict['spiderid'] == 'walkerplus_movie':
                message_count += 1

        self.assertEqual(message_count, 1)

    def test_showing_booking_sample_crawl_job(self):
        showing_booking_sample_crawl_job(self.logger, self.settings)

        for spider_id in spider_setting:
            path = self.zookeeper_path + spider_id
            data = self.zookeeper.get(path)[0]
            data_dict = json.loads(data.decode('utf-8'))
            self.assertEqual(data_dict['use_sample'], True)
            self.assertEqual(data_dict['crawl_booking_data'], True)
            self.assertEqual(data_dict['crawl_all_cinemas'], False)
            self.assertEqual(data_dict['crawl_all_movies'], True)

        message_count = 0
        for m in self.consumer:
            if m is None:
                pass
            the_dict = json.loads(m.value)
            if the_dict is not None and 'url' in the_dict \
                    and the_dict['url'] \
                    and 'spiderid' in the_dict \
                    and the_dict['spiderid'] == 'walkerplus_movie':
                message_count += 1

        self.assertEqual(message_count, 1)

    def test_set_throttle_job(self):
        set_throttle_job(self.logger, self.settings)

        message_count = 0
        for m in self.consumer:
            if m is None:
                pass
            the_dict = json.loads(m.value)
            if the_dict is not None and 'url' in the_dict \
                    and the_dict['url'] \
                    and 'hits' in the_dict \
                    and the_dict['hits'] > 0:
                message_count += 1

        self.assertEqual(message_count, len(spider_setting))

    def tearDown(self):
        # make sure no test kafka message is left
        for m in self.jcss_consumer:
            pass
        self.jcss_consumer.close()
        for m in self.consumer:
            pass
        self.consumer.close()

        # clean zookeeper test data
        self.zookeeper.delete(
            self.settings['JCSS_ZOOKEEPER_PATH'], recursive=True)
        self.zookeeper.stop()
        self.zookeeper.close()


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
        send_job_to_kafka(self.topic, job)

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
        self.settings = {
            'JCSS_ZOOKEEPER_HOST': 'zookeeper:2181',
            'JCSS_ZOOKEEPER_PATH': '/test/',
            'JCSS_DEFAULT_MOVIES': ['movie1'],
            'JCSS_SAMPLE_CINEMAS': ['cinema1', 'cinema2'],
            'JCSS_DEFAULT_CINEMAS': {
                'testspider': ['defaultcinema']
            },
        }
        self.spiderid = 'testspider'
        self.full_path = self.settings['JCSS_ZOOKEEPER_PATH'] + self.spiderid
        self.zookeeper = KazooClient(
            hosts=self.settings['JCSS_ZOOKEEPER_HOST'])
        self.zookeeper.start()

    def test_change_spider_config(self):
        self.assertFalse(
            self.zookeeper.exists(self.settings['JCSS_ZOOKEEPER_PATH']))
        change_spider_config(
            spiderid=self.spiderid, settings=self.settings)
        self.assertTrue(self.zookeeper.exists(self.full_path))
        data = self.zookeeper.get(self.full_path)[0]
        d = json.loads(data.decode('utf-8'))
        self.assertEqual(d["use_sample"], False)
        self.assertEqual(d["crawl_booking_data"], False)
        self.assertEqual(
            d["movie_list"], self.settings['JCSS_DEFAULT_MOVIES'])

        change_spider_config(
            spiderid=self.spiderid, settings=self.settings,
            use_sample=True, crawl_booking_data=True)
        data = self.zookeeper.get(self.full_path)[0]
        d = json.loads(data.decode('utf-8'))
        self.assertEqual(d["use_sample"], True)
        self.assertEqual(d["crawl_booking_data"], True)
        self.assertEqual(
            d["cinema_list"], self.settings['JCSS_SAMPLE_CINEMAS'])

    def tearDown(self):
        # clean zookeeper test data
        self.zookeeper.delete(
            self.settings['JCSS_ZOOKEEPER_PATH'], recursive=True)
        self.zookeeper.stop()
        self.zookeeper.close()


if __name__ == '__main__':
    unittest.main()
