# -*- coding: utf-8 -*-
import datetime
import scrapy


class TohoSpider(scrapy.Spider):
    name = "toho_cinema"
    allowed_domains = ["hlo.tohotheater.jp", "www.tohotheater.jp"]
    start_urls = ['https://www.tohotheater.jp/theater/find.html']

    def parse(self, response):
        """
        crawl toho cinema info, mainly seats conut of each screen
        example: https://www.tohotheater.jp/theater/064/institution.html
        https://hlo.tohotheater.jp/net/schedule/064/TNPI2000J01.do
        """
        all_cinema_url = response.xpath('//h3[contains(text(),"地区")]'
                                        '/..//a[contains(@href,"schedule")]'
                                        '/@href')
        for curr_cinema_url in all_cinema_url:
            cinema_number = curr_cinema_url.re(r'/net/schedule/'
                                               '([0-9]+)/TNPI2000J01.do')
            tail_url = '/theater/'+cinema_number[0]+'/institution.html'
            cinema_page_url = response.urljoin(tail_url)
            request = scrapy.Request(cinema_page_url,
                                     callback=self.parse_cinema)
            yield request

    def parse_cinema(self, response):
        cinema_name = response.xpath(
            '//h1[@class="c-page_heading is-lv-01"]'
            '/span/text()').extract_first()
        all_screen_list = response.xpath(
            '//table[@class="c-table01 __table"]/tbody/tr')
        result = {}
        result['cinema_name'] = cinema_name
        for curr_screen in all_screen_list:
            screen_name = curr_screen.xpath(
                './td[position()=1]/text()').extract_first()
            screen_seat_number = curr_screen.xpath(
                './td[position()=2]/text()').extract_first()
            if screen_name is not None:
                result[screen_name] = screen_seat_number
        yield result
