import unittest
from mock import MagicMock, patch

from scrapy.http import Request
from scrapy import Item

from crawler.spidermiddlewares.reset_meta import ResetMetaMiddleware
from crawler.spidermiddlewares.debug_single_output import \
    DebugSingleOutputMiddleware


@patch("crawler.spidermiddlewares.reset_meta.sc_log_setup")
class TestResetMetaMiddleware(unittest.TestCase):
    def test_process_spider_output(self, sc_log_setup_mock):
        settings = MagicMock()
        middleware = ResetMetaMiddleware(settings)

        test_list = [
            {},
            Item(),
            Request('http://www.baidu.com'),
        ]
        result = []
        for output in middleware.process_spider_output(
                MagicMock(), test_list, MagicMock()):
            result.append(output)
        self.assertEqual(len(result), 3)
        self.assertTrue(isinstance(result[2], Request))
        self.assertTrue('dont_merge_cookies' not in result[2].meta)

        # when 'dont_merge_cookies' in parent response, should set
        # this value to False in request to avoid scrapy-cluster's
        # MetaPassthroughMiddleware to copy this meta which will change
        # default value
        response = MagicMock()
        response.meta = {'dont_merge_cookies': True}
        r = Request('http://www.baidu.com')
        for output in middleware.process_spider_output(
                response, [r], MagicMock()):
            self.assertFalse(output.meta['dont_merge_cookies'])

        # when 'dont_merge_cookies' is setted in request, should not
        # change it
        r = Request('http://www.baidu.com')
        r.meta['dont_merge_cookies'] = True
        for output in middleware.process_spider_output(
                response, [r], MagicMock()):
            self.assertTrue(output.meta['dont_merge_cookies'])


@patch("crawler.spidermiddlewares.debug_single_output.sc_log_setup")
class TestDebugSingleOutputMiddleware(unittest.TestCase):
    def test_process_spider_output(self, sc_log_setup_mock):
        settings = MagicMock()
        middleware = DebugSingleOutputMiddleware(settings)
        result = []
        for output in middleware.process_spider_output(
                MagicMock(), iter(MagicMock(), MagicMock()), MagicMock()):
            result.append(output)
        self.assertEqual(len(result), 1)
