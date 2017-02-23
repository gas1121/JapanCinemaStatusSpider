# -*- coding: utf-8 -*-
import scrapy
from scrapyproject.items import (Cinema, standardize_cinema_name,
                                 standardize_screen_name)


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
        all_areas = response.xpath('//h3[contains(text(),"地区")]/..')
        for curr_area in all_areas:
            area = curr_area.xpath('./h3/text()').extract_first()
            area_en = curr_area.xpath('./h3/span/text()').extract_first()
            all_counties = curr_area.xpath('./div//section')
            for curr_county in all_counties:
                county = curr_county.xpath('./h4/text()').extract_first()
                county_en = curr_county.xpath(
                    './h4/span/text()').extract_first()
                all_cinema_url = curr_county.xpath(
                    './/a[contains(@href,"schedule")]/@href')
                for curr_cinema_url in all_cinema_url:
                    cinema_number = curr_cinema_url.re(
                        r'/net/schedule/([0-9]+)/TNPI2000J01.do')
                    tail_url = '/theater/'+cinema_number[0]+'/institution.html'
                    tail_url = '/theater/034/institution.html'
                    cinema_page_url = response.urljoin(tail_url)
                    request = scrapy.Request(cinema_page_url,
                                             callback=self.parse_cinema)
                    request.meta['area'] = area
                    request.meta['area_en'] = area_en
                    request.meta['county'] = county
                    request.meta['county_en'] = county_en
                    #yield request
                    return request

    def parse_cinema(self, response):
        # TODO one of cinemas is missing
        cinema_name = response.xpath(
            '//h1[@class="c-page_heading is-lv-01"]'
            '/span/text()').extract_first()
        cinema = Cinema()
        cinema['name'] = standardize_cinema_name(cinema_name)
        cinema['screens'] = {}
        cinema['area'] = response.meta['area']
        cinema['area_en'] = response.meta['area_en']
        cinema['county'] = response.meta['county']
        cinema['county_en'] = response.meta['county_en']
        # some cinemas have detail page and need to forward
        sub_page_list = response.xpath(
            '//section[@class="about"]//a[@class="link bold"]/@href').extract()
        for sub_page_url in sub_page_list:
            sub_page_url = response.urljoin(sub_page_url)
            request = scrapy.Request(sub_page_url,
                                     callback=self.parse_sub_cinema)
            request.meta['cinema'] = cinema.copy()
            print(request.meta['cinema'])
            yield request
        else:
            self.parse_seat_number_list(response, cinema)
            yield cinema

    def parse_sub_cinema(self, response):
        # TODO BUG 
        print("parse_sub_cinema")
        cinema = response.meta['cinema'].copy()
        print(cinema)
        self.parse_seat_number_list(response, cinema)
        # sub cinema use its own name
        cinema_name = response.xpath(
            '//div[@id="more-anchor-01"]/h4/text()').extract_first()
        cinema['name'] = standardize_cinema_name(cinema_name)
        yield cinema

    def parse_seat_number_list(self, response, cinema):
        all_screen_list = response.xpath(
            '//table[contains(@class,"c-table01")]/tbody/tr')
        # except total seats line
        all_screen_list = all_screen_list[:-1]
        for curr_screen in all_screen_list:
            screen_name = curr_screen.xpath(
                './td[1]/text()').extract_first()
            screen_name = standardize_screen_name(screen_name)
            if screen_name is not None:
                screen_seat_number_list = curr_screen.xpath(
                    './td[2]/text()').re(r'([0-9]+)[\+\＋]\(([0-9]+)\)')
                screen_seat_number = (int(screen_seat_number_list[0])
                                      + int(screen_seat_number_list[1]))
                cinema['screens'][screen_name] = screen_seat_number
