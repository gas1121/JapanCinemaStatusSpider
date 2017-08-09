import unittest
from mock import MagicMock, patch

from crawler.middlewares.cookies import RedisCookiesMiddleware
from crawler.middlewares.proxy import ProxyDownloaderMiddleware
from crawler.middlewares.selenium import SeleniumDownloaderMiddleware


class TestRedisCookiesMiddleware(unittest.TestCase):
    def test_process_request(self):
        # TODO
        pass

    def test_process_response(self):
        # TODO
        pass


class TestProxyDownloaderMiddleware(unittest.TestCase):
    @patch('crawler.middlewares.proxy.sc_log_setup', MagicMock())
    @patch('crawler.middlewares.proxy.do_proxy_request')
    def test_process_request(self, do_proxy_request_mock):
        proxy = ProxyDownloaderMiddleware(MagicMock())
        # pass when 'use_proxy' is False
        spider = MagicMock()
        spider.loaded_config = {'use_proxy': False}
        proxy.process_request(MagicMock(), spider)
        do_proxy_request_mock.assert_not_called()

        # TODO case when 'use_proxy' is True


class TestSeleniumDownloaderMiddleware(unittest.TestCase):
    @patch('crawler.middlewares.selenium.webdriver')
    def test_process_request(self, webdriver_mock):
        selenium = SeleniumDownloaderMiddleware()
        # pass when 'require_js' is False
        spider = MagicMock()
        spider.loaded_config = {'require_js': False}
        selenium.process_request(MagicMock(), spider)
        webdriver_mock.Remote.assert_not_called()

        # TODO case when 'require_js' is True
