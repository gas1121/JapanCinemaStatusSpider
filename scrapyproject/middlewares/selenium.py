from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


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
