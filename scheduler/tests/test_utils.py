import unittest

from scheduler import utils


class TestUtils(unittest.TestCase):
    def test_create_crawl_job(self):
        url = "testurl"
        spiderid = "testspiderid"
        appid = "testappid"
        crawlid = "testcrawlid"
        data = utils.create_crawl_job(
            url=url, spiderid=spiderid, appid=appid, crawlid=crawlid)
        self.assertEqual(data["url"], url)
        self.assertEqual(data["spiderid"], spiderid)
        self.assertEqual(data["appid"], appid)
        self.assertEqual(data["crawlid"], crawlid)

    def test_send_job_to_kafka(self):
        # TODO
        pass

    def test_change_spider_config(self):
        # TODO
        pass
