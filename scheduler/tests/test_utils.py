import unittest

import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from scheduler import utils


class TestCreateCrawlJob(unittest.TestCase):
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
