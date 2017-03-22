from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from scrapyproject.utils.site_utils import do_proxy_request


class SeleniumDownloaderMiddleware(object):
    """
    middleware to use phantomjs for site that need javascript support
    """
    def process_request(self, request, spider):
        if not hasattr(spider, 'require_js'):
            return
        driver = webdriver.Remote(
                command_executor='http://phantomjs:8910',
                desired_capabilities=DesiredCapabilities.PHANTOMJS
            )
        driver.get(request.url)
        body = driver.page_source
        url = driver.current_url
        driver.close()
        return HtmlResponse(url, body=body, request=request, encoding='utf-8')


class ProxyDownloaderMiddleware(object):
    """
    middleware for sites that need proxy to visit
    enabled when spider has attribute 'keep_old_data'
    """
    def process_request(self, request, spider):
        if (hasattr(spider, 'use_proxy')):
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
        else:
            return
