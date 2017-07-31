from scrapy.downloadermiddlewares.cookies import CookiesMiddleware


class CustomCookiesMiddleware(CookiesMiddleware):
    """
    get cookie from redis so those cookies can be shared across cluster
    """
    def process_request(self, request, spider):
        """
        Process request: deepcopy cookiejar.
        """
        if 'dont_merge_cookies' in request.meta:
            return
        # TODO get cookie from redis with related info as key
