import unittest
from mock import MagicMock, patch

from scrapy.http import HtmlResponse
from scrapy.http import Request

from crawler.spidermiddlewares.reset_meta import ResetMetaMiddleware
from crawler.spidermiddlewares.debug_single_output import \
    DebugSingleOutputMiddleware


class TestResetMetaMiddleware(unittest.TestCase):
    pass


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
