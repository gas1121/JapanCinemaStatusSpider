from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import scrapy


def test_parse(response):
    movieSection = response.xpath(
        '//div[contains(text(),"KIMINONAWA")]/../../..'
        )
    allSessionUrlItems = movieSection.xpath(
        '//a[@class="wrapper"]/@href')
    for currSessionUrlItem in allSessionUrlItems:
        print(currSessionUrlItem)
        url = generate_session_url(currSessionUrlItem)
        print(url)


def generate_session_url(currSessionUrlItem):
    parameters = currSessionUrlItem.re(r'purchaseTicket\("([0-9]+)", '
                                       '"([0-9]+)", "([0-9]+)", '
                                       '"([0-9]+)", "([0-9]+)", '
                                       '"([0-9]+)"\)')
    print(parameters)
    return "https://hlo.tohotheater.jp/net/ticket/076/"\
           "TNPI2040J03.do?site_cd={site_cd}&jyoei_date={jyoei_date}"\
           "&gekijyo_cd={gekijyo_cd}&screen_cd={screen_cd}"\
           "&sakuhin_cd={sakuhin_cd}&pf_no={pf_no}&fnc={fnc}"\
           "&pageid={pageid}&enter_kbn={enter_kbn}".format(
               site_cd=parameters[1], jyoei_date=parameters[0],
               gekijyo_cd=parameters[3], screen_cd=parameters[4],
               sakuhin_cd=parameters[2], pf_no=parameters[5],
               fnc="1", pageid="2000J01", enter_kbn="")


driver = webdriver.Remote(
                command_executor='http://phantomjs:8910',
                desired_capabilities=DesiredCapabilities.PHANTOMJS
            )
cinema_page_url = 'https://hlo.tohotheater.jp/net/schedule/076/TNPI2000J01.do'
print(cinema_page_url)
driver.get(cinema_page_url)
dateElement = driver.find_element_by_xpath('//div[@id="20170212"]')
dateElement.click()
body = driver.page_source
print(body)
request = scrapy.Request(cinema_page_url, callback=test_parse)
response = scrapy.http.HtmlResponse(driver.current_url, body=body,
                                    request=request, encoding='utf-8')
test_parse(response)
