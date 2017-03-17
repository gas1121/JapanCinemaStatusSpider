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


class ProxyDownloaderMiddleware:
    """
    middleware for sites that need proxy to visit
    enabled when spider has attribute 'keep_old_data'
    """
    def process_request(self, request, spider):
        # TODO fix form post problem for useing requests
        print(request.url)
        print(request.method)
        if request.method == "POST":
            print(request.__dict__)
        if (hasattr(spider, 'use_proxy')):
            r = do_proxy_request(request.url, cookies=request.cookies)
            return HtmlResponse(request.url, body=r.text,
                                request=request, encoding='utf-8')
        else:
            return
