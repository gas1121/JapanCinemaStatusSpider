from scrapy.http import Request
from scrapy.downloadermiddlewares.cookies import CookiesMiddleware
from scrapy.http.cookies import CookieJar
from crawler.utils import sc_log_setup


class CookieMiddleware(object):

    def __init__(self, settings):
        self.setup(settings)
        self.cookies_middleware = CookiesMiddleware(
            settings.getbool('COOKIES_DEBUG'))

    def setup(self, settings):
        '''
        Does the actual setup of the middleware
        '''
        # set up the default sc logger
        self.logger = sc_log_setup(settings)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def process_spider_output(self, response, result, spider):
        '''
        Do what default CookiesMiddleware does but do it in spider output
        side. This is needed because maybe a different spider will handle
        these requests and jar is useless in this situation
        '''
        self.logger.debug("processing cookie spider middleware")
        for x in result:
            # only operate on requests
            if isinstance(x, Request):
                self.logger.debug("found request")
                if not x.meta.get('dont_merge_cookies', False):
                    self.logger.debug("begin processing cookie")
                    jar = CookieJar()
                    jar.extract_cookies(response, x)
                    cookies = self.cookies_middleware._get_request_cookies(
                        jar, x)
                    self.logger.debug("request cookie: {}".format(cookies))
                    for cookie in cookies:
                        jar.set_cookie_if_ok(cookie, x)
                    # set Cookie header
                    x.headers.pop('Cookie', None)
                    jar.add_cookie_header(x)
            yield x
