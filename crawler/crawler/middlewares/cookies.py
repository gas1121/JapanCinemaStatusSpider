import redis
import json

import requests
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
        if request.meta.get('dont_merge_cookies', False):
            return
        # get cookie from redis if exist
        cookiejarkey = request.meta.get("cookiejar")
        key = self._get_key(spider, cookiejarkey=cookiejarkey)
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
        if request.meta.get('dont_merge_cookies', False):
            return response

        # get cookie from redis if exist
        cookiejarkey = request.meta.get("cookiejar")
        key = self._get_key(spider, cookiejarkey=cookiejarkey)
        jar = self._get_cookie_from_redis(key)
        # extract cookies from Set-Cookie and drop invalid/expired cookies
        jar.extract_cookies(response, request)
        # store cookie to redis
        self._store_cookie_to_redis(key, jar)

        self._debug_set_cookie(response, spider)

        return response

    def _get_key(self, spider, cookiejarkey=None):
        """
        get key for cookies in redis
        """
        return "cookie:{}:{}:{}".format(
            spider.name, spider.uuid, cookiejarkey if cookiejarkey else "all")

    def _get_cookie_from_redis(self, key):
        """
        get stored cookiejar if exist, else return a new cookie
        """
        cookiejar = CookieJar()
        if self.redis_conn.exists(key):
            exist_data = self.redis_conn.get(key)
            cookie_dict = json.loads(exist_data)
            cookiejar = requests.utils.add_dict_to_cookiejar(
                cookiejar, cookie_dict)
        return cookiejar

    def _store_cookie_to_redis(self, key, cookiejar):
        """
        store a exist cookiejar into redis
        """
        cookie_dict = requests.utils.dict_from_cookiejar(cookiejar)
        self.redis_conn.set(key, json.dumps(cookie_dict))
