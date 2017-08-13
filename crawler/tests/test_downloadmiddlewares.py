import unittest
from mock import MagicMock, patch
import pickle

from scrapy.utils.project import get_project_settings
from scrapy.http.cookies import CookieJar

from crawler.middlewares.cookies import RedisCookiesMiddleware
from crawler.middlewares.proxy import ProxyDownloaderMiddleware
from crawler.middlewares.selenium import SeleniumDownloaderMiddleware


@patch('crawler.middlewares.proxy.sc_log_setup', MagicMock())
class TestRedisCookiesMiddleware(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('crawler.middlewares.cookies.redis')
        self.redis_mock = self.patcher.start()
        self.redis_conn = MagicMock()
        self.redis_mock.Redis.return_value = self.redis_conn

        settings = get_project_settings()
        settings.set('COOKIES_ENABLED', True)
        settings.set('COOKIES_DEBUG', True)
        crawler = MagicMock()
        crawler.settings = settings
        self.middleware = RedisCookiesMiddleware.from_crawler(crawler)

    def test_process_request(self):
        request = MagicMock()
        request.meta = {
            'dont_merge_cookies': False,
            'cookiejar': None,
        }
        spider = MagicMock()
        self.middleware._get_key = MagicMock(return_value='test-key')
        jar = MagicMock()
        self.middleware._get_cookie_from_redis = MagicMock(return_value=jar)
        self.middleware._get_request_cookies = MagicMock()
        self.middleware._store_cookie_to_redis = MagicMock()
        self.middleware._debug_cookie = MagicMock()
        self.middleware.process_request(request, spider)
        self.middleware._get_key.assert_called_once_with(
            spider, cookiejarkey=None)
        self.middleware._get_cookie_from_redis.assert_called_once_with(
            'test-key')
        self.middleware._get_request_cookies.assert_called_once_with(
            jar, request)
        self.middleware._store_cookie_to_redis.assert_called_once_with(
            'test-key', jar)

    def test_process_response(self):
        request = MagicMock()
        request.meta = {
            'dont_merge_cookies': False,
            'cookiejar': None,
        }
        spider = MagicMock()
        self.middleware._get_key = MagicMock(return_value='test-key')
        jar = MagicMock()
        self.middleware._get_cookie_from_redis = MagicMock(return_value=jar)
        self.middleware._store_cookie_to_redis = MagicMock()
        self.middleware._debug_cookie = MagicMock()
        self.middleware.process_response(request, MagicMock(), spider)
        self.middleware._get_key.assert_called_once_with(
            spider, cookiejarkey=None)
        self.middleware._get_cookie_from_redis.assert_called_once_with(
            'test-key')
        self.middleware._store_cookie_to_redis.assert_called_once_with(
            'test-key', jar)

    def test_get_key(self):
        spider = MagicMock()
        spider.name = 'test'
        spider.uuid = 'uuid'
        key = self.middleware._get_key(spider, cookiejarkey=None)
        self.assertEqual(key, 'cookie:test:uuid:all')
        key = self.middleware._get_key(spider, cookiejarkey='key')
        self.assertEqual(key, 'cookie:test:uuid:key')

    def test_get_cookie_from_redis(self):
        self.redis_conn.exists.return_value = False
        key = 'test'
        jar = self.middleware._get_cookie_from_redis(key)
        self.assertFalse(jar._cookies)

        self.redis_conn.exists.return_value = True
        exist_jar = CookieJar()
        exist_jar._cookies['key'] = 'value'
        self.redis_conn.get.return_value = pickle.dumps(
            exist_jar).decode('latin1')
        jar = self.middleware._get_cookie_from_redis(key)
        self.assertEqual(jar._cookies['key'], 'value')

    def test_store_cookie_to_redis(self):
        self.redis_conn.set = MagicMock()
        jar = CookieJar()
        self.middleware._store_cookie_to_redis('test', jar)
        self.redis_conn.set.assert_called_once_with(
            'test', pickle.dumps(jar).decode('latin1'))

    def tearDown(self):
        self.patcher.stop()


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
