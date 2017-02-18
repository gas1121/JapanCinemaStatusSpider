# -*- coding: utf-8 -*-
import scrapy
from scrapyproject.items import Cinema


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
        cinema = Cinema()
        cinema['name'] = cinema_name
        cinema['screens'] = {}
        # some cinemas have detail page and need to forward
        sub_page_list = response.xpath(
            '//section[@class="about"]//a[@class="link bold"]/@href').extract()
        if sub_page_list:
            curr_page_url = response.urljoin(sub_page_list[0])
            request = scrapy.Request(curr_page_url,
                                     callback=self.parse_sub_cinema)
            request.meta['cinema'] = cinema
            request.meta['remain_page_list'] = sub_page_list[1:]
            yield request
        else:
            self.parse_seat_number_list(response, cinema)
            yield cinema

    def parse_sub_cinema(self, response):
        self.parse_seat_number_list(response, response.meta['cinema'])
        remain_page_list = response.meta['remain_page_list']
        if remain_page_list:
            curr_page_url = remain_page_list[0]
            request = scrapy.Request(curr_page_url,
                                     callback=self.parse_sub_cinema)
            request.meta['remain_page_list'] = remain_page_list[1:]
            request.meta['cinema'] = response.meta['cinema']
            yield request
        else:
            yield response.meta['cinema']

    def parse_seat_number_list(self, response, cinema):
        all_screen_list = response.xpath(
            '//table[contains(@class,"c-table01")]/tbody/tr')
        # except total seats line
        all_screen_list = all_screen_list[:-1]
        for curr_screen in all_screen_list:
            screen_name = curr_screen.xpath(
                './td[1]/text()').extract_first()
            if screen_name is not None:
                screen_seat_number_list = curr_screen.xpath(
                    './td[2]/text()').re(r'([0-9]+)[\+\＋]\(([0-9]+)\)')
                screen_seat_number = (int(screen_seat_number_list[0])
                                      + int(screen_seat_number_list[1]))
                cinema['screens'][screen_name] = screen_seat_number
