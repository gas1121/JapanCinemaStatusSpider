from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class SeleniumDownloaderMiddleware(object):
    def process_request(self, request, spider):
        if spider.name == "toho":
            driver = webdriver.Remote(
                command_executor='http://phantomjs:8910',
                desired_capabilities=DesiredCapabilities.PHANTOMJS
            )
            driver.get(request.url)
            # if have selectDate meta item, do click action and wait
            if "selectDate" in request.meta:
                dateStr = str(request.meta["selectDate"])
                dateElement = driver.find_element_by_xpath(
                    '//div[@id="' + str(request.meta["selectDate"]) + '"]')
                singleDateStr = dateStr[-2:]
                dateElement.click()
                wait = WebDriverWait(driver, 10)
                wait.until(EC.element_to_be_clickable((
                    By.XPATH,
                    '//h3[@class="schedule-body-day"'
                    ' and contains(text(), "'+singleDateStr+'")]'
                    )))
            body = driver.page_source
            return HtmlResponse(driver.current_url, body=body,
                                request=request, encoding='utf-8')
        else:
            return
