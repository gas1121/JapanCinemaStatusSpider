import redis
from scrapy.http.cookies import CookieJar
from scrapy.exceptions import NotConfigured
from scrapy.downloadermiddlewares.cookies import CookiesMiddleware

from crawler.utils import sc_log_setup


class RedisCookiesMiddleware(CookiesMiddleware):
    """
    get cookie from redis so those cookies can be shared across cluster
    """
    def __init__(self, settings):
        # set up the default sc logger
        self.logger = sc_log_setup(settings)
        # set up redis
        self.redis_conn = redis.Redis(
            host=settings.get('REDIS_HOST'),
            port=settings.get('REDIS_PORT'),
            db=settings.get('REDIS_DB'),
            decode_responses=True)
        super(RedisCookiesMiddleware, self).__init__(
            settings.getbool('COOKIES_DEBUG'))

    @classmethod
    def from_crawler(cls, crawler):
        if not crawler.settings.getbool('COOKIES_ENABLED'):
            raise NotConfigured
        return cls(crawler.settings)

    def process_request(self, request, spider):
        """
        read cookies from redis when needed
        """
        if 'dont_merge_cookies' in request.meta:
            return
        jar = CookieJar()
        # TODO get cookie from redis
        cookies = self._get_request_cookies(jar, request)
        for cookie in cookies:
            jar.set_cookie_if_ok(cookie, request)
        # set Cookie header
        request.headers.pop('Cookie', None)
        jar.add_cookie_header(request)
        self._debug_cookie(request, spider)

    def process_response(self, request, response, spider):
        """
        store cookies to redis
        """
        if request.meta.get('dont_merge_cookies', False):
            return response

        # get cookie from redis if exist
        # TODO

        # extract cookies from Set-Cookie and drop invalid/expired cookies
        jar = CookieJar()
        jar.extract_cookies(response, request)
        # TODO store cookie to redis
        self._debug_set_cookie(response, spider)

        return response

    def _get_key(self, spider, cookiejarkey=None):
        """
        get key for cookies in redis
        """
        return "{}:{}:{}".format(
            spider.name, spider.my_ip, cookiejarkey if cookiejarkey else "all")

    def _get_cookie_from_redis(self, key):
        # TODO
        pass
