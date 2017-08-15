import unittest
from mock import MagicMock, patch
import json

import arrow

from scheduler.utils import (create_crawl_job, send_job_to_kafka,
                             change_spider_config, create_domain_throttle_job)


class TestUtils(unittest.TestCase):
    def test_create_domain_throttle_job(self):
        domain = "test.domain"
        data = create_domain_throttle_job(domain=domain)
        self.assertEqual(data["domain"], domain)
        self.assertEqual(data["action"], "domain-update")

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

    @patch("scheduler.utils.KazooClient")
    def test_change_spider_config(self, zookeeper_mock):
        instance_mock = MagicMock()
        zookeeper_mock.return_value = instance_mock
        instance_mock.exists = MagicMock(return_value=False)
        settings = {
            'JCSS_ZOOKEEPER_HOST': 'test',
            'JCSS_ZOOKEEPER_PATH': '/test/',
            'JCSS_DEFAULT_MOVIES': ['movie1'],
            'JCSS_SAMPLE_CINEMAS': ['cinema1', 'cinema2'],
            'JCSS_DEFAULT_CINEMAS': {
                'testid': ['defaultcinema']
            },
        }
        change_spider_config(
            spiderid="testid", settings=settings, use_sample=False,
            crawl_booking_data=False)

        expected_path = "/test/testid"
        expected_data = json.dumps({
            "use_sample": False,
            "crawl_booking_data": False,
            "use_proxy": False,
            "require_js": False,
            "crawl_all_cinemas": False,
            "crawl_all_movies": False,
            "movie_list": ['movie1'],
            "cinema_list": ['defaultcinema'],
            "date": arrow.now('UTC+9').shift(days=+1).format('YYYYMMDD'),
        }).encode('utf-8')
        instance_mock.ensure_path.assert_called_once_with(expected_path)
        instance_mock.set.assert_called_once_with(expected_path, expected_data)
        instance_mock.set.reset_mock()

        # ignore when old data exists but is empty
        instance_mock.exists = MagicMock(return_value=True)
        instance_mock.get = MagicMock(return_value=[b""])
        change_spider_config(
            spiderid="testid", settings=settings, use_sample=True,
            crawl_booking_data=False, movie_list=['newmovie'])
        instance_mock.get.assert_called_once_with(expected_path)
        expected_data = json.dumps({
            "use_sample": True,
            "crawl_booking_data": False,
            "use_proxy": False,
            "require_js": False,
            "crawl_all_cinemas": False,
            "crawl_all_movies": False,
            "movie_list": ['newmovie'],
            "cinema_list": settings['JCSS_SAMPLE_CINEMAS'],
            "date": arrow.now('UTC+9').shift(days=+1).format('YYYYMMDD'),
        }).encode('utf-8')
        instance_mock.set.assert_called_once_with(expected_path, expected_data)
        instance_mock.set.reset_mock()

        instance_mock.exists = MagicMock(return_value=True)
        old_dict = {
            'use_sample': False
        }
        old_data = json.dumps(old_dict).encode('utf-8')
        instance_mock.get = MagicMock(return_value=[old_data])
        change_spider_config(
            spiderid="testid", settings=settings, use_sample=True,
            crawl_booking_data=False, movie_list=['newmovie'])
        instance_mock.get.assert_called_once_with(expected_path)
        expected_data = json.dumps({
            "use_sample": True,
            "crawl_booking_data": False,
            "use_proxy": False,
            "require_js": False,
            "crawl_all_cinemas": False,
            "crawl_all_movies": False,
            "movie_list": ['newmovie'],
            "cinema_list": settings['JCSS_SAMPLE_CINEMAS'],
            "date": arrow.now('UTC+9').shift(days=+1).format('YYYYMMDD'),
        }).encode('utf-8')
        instance_mock.set.assert_called_once_with(expected_path, expected_data)
        instance_mock.set.reset_mock()

        instance_mock.exists = MagicMock(return_value=False)
        change_spider_config(
            spiderid="testid", settings=settings, use_sample=False,
            crawl_booking_data=False, cinema_list=['newcinema'],
            date='20170101')
        instance_mock.get.assert_called_once_with(expected_path)
        expected_data = json.dumps({
            "use_sample": False,
            "crawl_booking_data": False,
            "use_proxy": False,
            "require_js": False,
            "crawl_all_cinemas": False,
            "crawl_all_movies": False,
            "movie_list": ['movie1'],
            "cinema_list": ['newcinema'],
            "date": '20170101',
        }).encode('utf-8')
        instance_mock.set.assert_called_once_with(expected_path, expected_data)
        instance_mock.set.reset_mock()
