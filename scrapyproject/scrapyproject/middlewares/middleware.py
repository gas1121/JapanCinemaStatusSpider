from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


class SeleniumDownloaderMiddleware(object):
    def process_request(self, request, spider):
        if spider.name == "toho":
            driver = webdriver.Remote(
                command_executor='http://phantomjs:8910',
                desired_capabilities=DesiredCapabilities.PHANTOMJS
            )
            driver.get(request.url)
            body = driver.page_source
            return HtmlResponse(driver.current_url, body=body,
                                request=request, encoding='utf-8')
        else:
            return
