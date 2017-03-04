import os
from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests


class SeleniumDownloaderMiddleware(object):
    """
    middleware to use phantomjs for site that need javascript support
    """
    def process_request(self, request, spider):
        if spider.name == "toho" or spider.name == "toho_cinema":
            driver = webdriver.Remote(
                command_executor='http://phantomjs:8910',
                desired_capabilities=DesiredCapabilities.PHANTOMJS
            )
            driver.get(request.url)
            # if have selectDate meta item, do click action and wait
            if "selectDate" in request.meta:
                dateStr = request.meta["selectDate"]
                try:
                    # wait page totally loaded first
                    wait = WebDriverWait(driver, 10)
                    wait.until(EC.element_to_be_clickable((
                        By.XPATH,
                        '//div[@class="schedule-tab-item"]'
                        )))
                    dateElement = driver.find_element_by_xpath(
                        '//div[@id="' + dateStr + '"]')
                    singleDateStr = dateStr[-2:]
                    dateElement.click()
                    wait = WebDriverWait(driver, 10)
                    wait.until(EC.element_to_be_clickable((
                        By.XPATH,
                        '//h3[@class="schedule-body-day"'
                        ' and contains(text(), "'+singleDateStr+'")]'
                        )))

                    # TOHOシネマズ ららぽーと横浜 have a node that
                    # has too much depth which will lead spider fail to crawl.
                    # so we need to remove part of the page before using it.
                    driver.execute_script("""
                    var currlist = document.evaluate("//section[@class='news']"
                    ,document, null, XPathResult.ANY_TYPE, null);
                    var element = currlist.iterateNext()
                    if (element) {
                        element.parentNode.removeChild(element);
                    }
                    """)
                except NoSuchElementException:
                    driver.close()
                    return
            body = driver.page_source
            url = driver.current_url
            driver.close()
            return HtmlResponse(url, body=body,
                                request=request, encoding='utf-8')
        else:
            return


class ProxyDownloaderMiddleware:
    """
    middleware for sites that need proxy to visit
    enabled when spider has attribute 'keep_old_data'
    """
    proxy_type = os.environ['PROXY_TYPE']
    proxy_address = os.environ['PROXY_ADDRESS']
    proxy_port = os.environ['PROXY_PORT']

    def __init__(self):
        self.proxy_str = (self.proxy_type + '://user:pass@'
                          + self.proxy_address + ':' + self.proxy_port)

    def process_request(self, request, spider):
        if (hasattr(spider, 'use_proxy')):
            proxies = {
                'http': self.proxy_str,
                'https': self.proxy_str
            }
            r = requests.get(request.url, proxies=proxies)
            return HtmlResponse(request.url, body=r.text,
                                request=request, encoding='utf-8')
        else:
            return
