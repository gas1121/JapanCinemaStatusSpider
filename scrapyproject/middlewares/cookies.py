"""
Custom cookie middleware, add cookiejar deriving support to origin middleware
"""
from copy import deepcopy
from scrapy.downloadermiddlewares.cookies import CookiesMiddleware
from scrapy.exceptions import NotConfigured


class CustomCookiesMiddleware(object):
    """
    middleware to use phantomjs for site that need javascript support
    """
    def __init__(self, debug=False):
        self._cookies_middleware = CookiesMiddleware(debug=debug)

    @classmethod
    def from_crawler(cls, crawler):
        # Copied from scrapy/downloadermiddlewares/cookies.py
        if not crawler.settings.getbool('COOKIES_ENABLED'):
            raise NotConfigured
        return cls(crawler.settings.getbool('COOKIES_DEBUG'))

    @property
    def _jars(self):
        """
        Get direct access to :att:`jars` to wrapped middleware.
        """
        return self._cookies_middleware.jars

    def process_request(self, request, spider):
        """
        Process request: deepcopy cookiejar.
        """
        # Deep copy cookiejar if request.meta['copied_cookiejar']
        if 'copied_cookiejar' in request.meta:
            # Ensure request.meta['cookiejar'] is set
            assert 'cookiejar' in request.meta

            copied_cookiejar_key = request.meta['copied_cookiejar']
            # Ensure cookiejar to copy already exist
            assert copied_cookiejar_key in self._jars

            # Perform deepcopy
            self._jars[request.meta['cookiejar']] = \
                deepcopy(self._jars[copied_cookiejar_key])

        self._cookies_middleware.process_request(request, spider)

    def process_response(self, request, response, spider):
        return self._cookies_middleware.process_response(request, response,
                                                         spider)
