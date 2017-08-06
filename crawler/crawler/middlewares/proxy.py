from scrapy.http import HtmlResponse
from crawler.utils import do_proxy_request
from crawler.utils import sc_log_setup


class ProxyDownloaderMiddleware(object):
    """
    middleware for sites that need proxy to visit
    enabled when spider has attribute 'use_proxy'
    """
    def __init__(self, settings):
        '''
        Does the actual setup of the middleware
        '''
        # set up the default sc logger
        self.logger = sc_log_setup(settings)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def process_request(self, request, spider):
        self.logger.debug("processing proxy downloader middleware")
        if not spider.use_proxy:
            return
        # convert 'cookie' in headers to 'Cookie' as requests library
        # do not recognize the former one
        # see cookiejar.py in requests library
        headers = request.headers.to_unicode_dict()
        if 'cookie' in headers and 'Cookie' not in headers:
            headers['Cookie'] = headers.pop('cookie')
        r = do_proxy_request(url=request.url, method=request.method,
                             data=request.body,
                             headers=headers,
                             cookies=request.cookies)
        headers = {}
        if 'Set-Cookie' in r.headers:
            headers['Set-Cookie'] = [r.headers['Set-Cookie']]
        return HtmlResponse(request.url, body=r.text, headers=headers,
                            request=request, encoding="utf-8")
