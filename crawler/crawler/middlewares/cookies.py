import redis
import pickle

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
        self.logger.debug("{}: process_request".format(
            self.__class__.__name__))
        if request.meta.get('dont_merge_cookies', False):
            return
        # set cookiejar_id to source spider's uuid if not already set
        if 'cookiejar_id' not in request.meta:
            request.meta['cookiejar_id'] = spider.uuid
        cookiejar_id = request.meta.get('cookiejar_id')
        # get cookie from redis if exist
        cookiejarkey = request.meta.get("cookiejar")
        key = self._get_key(
            spider.name, cookiejar_id, cookiejarkey=cookiejarkey)
        jar = self._get_cookie_from_redis(key)
        cookies = self._get_request_cookies(jar, request)
        for cookie in cookies:
            jar.set_cookie_if_ok(cookie, request)
        # set Cookie header
        request.headers.pop('Cookie', None)
        jar.add_cookie_header(request)
        # store cookie to redis
        self._store_cookie_to_redis(key, jar)
        self._debug_cookie(request, spider)

    def process_response(self, request, response, spider):
        """
        store cookies to redis
        """
        self.logger.debug("{}: process_response".format(
            self.__class__.__name__))
        if request.meta.get('dont_merge_cookies', False):
            return response
        # set cookiejar_id to source spider's uuid if not already set
        if 'cookiejar_id' not in request.meta:
            request.meta['cookiejar_id'] = spider.uuid
        # get cookie from redis if exist
        cookiejar_id = request.meta.get('cookiejar_id')
        cookiejarkey = request.meta.get("cookiejar")
        key = self._get_key(
            spider.name, cookiejar_id, cookiejarkey=cookiejarkey)
        jar = self._get_cookie_from_redis(key)
        # extract cookies from Set-Cookie and drop invalid/expired cookies
        jar.extract_cookies(response, request)
        # store cookie to redis
        self._store_cookie_to_redis(key, jar)

        self._debug_set_cookie(response, spider)

        return response

    def _get_key(self, spider_name, cookiejar_id, cookiejarkey=None):
        """
        get key for cookies in redis
        @param cookiejar_id uuid of cookiejar, one for each spider instance
        @param cookiejarkey extra key string of cookiejar
        """
        # keep spider name for ease of cleaning in test
        return "cookie:{}:{}:{}".format(
            spider_name, cookiejar_id,
            cookiejarkey if cookiejarkey else "all")

    def _get_cookie_from_redis(self, key):
        """
        get stored cookiejar if exist, else return a new cookie
        """
        if self.redis_conn.exists(key):
            exist_data = self.redis_conn.get(key)
            return pickle.loads(exist_data.encode('latin1'))
        else:
            return CookieJar()

    def _store_cookie_to_redis(self, key, cookiejar):
        """
        store a exist cookiejar into redis
        """
        self.redis_conn.set(key, pickle.dumps(cookiejar).decode('latin1'))
        # set expire time for cookiejar in redis
        self.redis_conn.expire(key, 60*60)
