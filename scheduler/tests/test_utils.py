import unittest
from mock import MagicMock, patch
import json

from scheduler.utils import (create_crawl_job, send_job_to_kafka,
                             change_spider_config)


class TestUtils(unittest.TestCase):
    def test_create_crawl_job(self):
        url = "testurl"
        spiderid = "testspiderid"
        appid = "testappid"
        crawlid = "testcrawlid"
        data = create_crawl_job(
            url=url, spiderid=spiderid, appid=appid, crawlid=crawlid)
        self.assertEqual(data["url"], url)
        self.assertEqual(data["spiderid"], spiderid)
        self.assertEqual(data["appid"], appid)
        self.assertEqual(data["crawlid"], crawlid)

    @patch("scheduler.utils.KafkaMonitor", autospec=True)
    def test_send_job_to_kafka(self, kafka_monitor_mock):
        instance_mock = MagicMock()
        kafka_monitor_mock.return_value = instance_mock
        topic = 'test_topic'
        job = {
            'data': 'test'
        }
        send_job_to_kafka(topic, job)
        instance_mock.feed.assert_called_once_with(job)

    @patch("scheduler.utils.zookeeper_file_path", new="/test/")
    @patch("scheduler.utils.KazooClient")
    def test_change_spider_config(self, zookeeper_mock):
        instance_mock = MagicMock()
        zookeeper_mock.return_value = instance_mock
        instance_mock.exists = MagicMock(return_value=False)
        change_spider_config(
            spiderid="testid", use_sample=False, crawl_booking_data=False)

        expected_path = "/test/testid"
        expected_data = json.dumps({
            "use_sample": False,
            "crawl_booking_data": False,
        }).encode('utf-8')
        instance_mock.ensure_path.assert_called_once_with(expected_path)
        instance_mock.set.assert_called_once_with(expected_path, expected_data)

        instance_mock.exists = MagicMock(return_value=True)
        old_dict = {
            'use_sample': False
        }
        old_data = json.dumps(old_dict).encode('utf-8')
        instance_mock.get = MagicMock(return_value=[old_data])
        change_spider_config(
            spiderid="testid", use_sample=True, crawl_booking_data=False)
        instance_mock.get.assert_called_once_with(expected_path)
        self.assertEqual(instance_mock.set.call_count, 2)
        expected_data = json.dumps({
            "use_sample": True,
            "crawl_booking_data": False,
        }).encode('utf-8')
        instance_mock.set.assert_called_with(expected_path, expected_data)
