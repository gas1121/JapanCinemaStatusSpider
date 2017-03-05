# -*- coding: utf-8 -*-
import re
import unicodedata
import scrapy
from scrapyproject.items import Cinema
from scrapyproject.utils.spider_helper import CinemasDatabaseMixin


class EigaCinemaSpider(scrapy.Spider, CinemasDatabaseMixin):
    """
    spider to crawl cinema info from http://eiga.com
    """
    name = "eiga_cinema"
    allowed_domains = ["eiga.com"]
    start_urls = ['http://eiga.com/theater/']

    def parse(self, response):
        """
        crawl cinema data from http://eiga.com/theater/
        """
        area_list = response.xpath('//dl[@id="list_b"]/dt')
        county_per_area_list = response.xpath('//dl[@id="list_b"]/dd')
        for i in range(len(area_list)):
            area_name = area_list[i].xpath('./text()').extract_first()
            county_list = county_per_area_list[i].xpath('.//a')
            for curr_county in county_list:
                county_name = curr_county.xpath('./text()').extract_first()
                url = curr_county.xpath('./@href').extract_first()
                url = response.urljoin(url)
                request = scrapy.Request(url,
                                         callback=self.parse_county)
                request.meta['area_name'] = area_name
                request.meta['county_name'] = county_name
                yield request
                #return request

    def parse_county(self, response):
        city_list = response.xpath('//div[@id="pref_theaters"]/h4')
        cinema_per_city_list = response.xpath('//div[@id="pref_theaters"]/ul')
        for i in range(len(city_list)):
            city_name = city_list[i].xpath('./text()').extract_first()
            city_name = re.sub(r"^(.+)の映画館$", r"\1", city_name)
            cinema_list = cinema_per_city_list[i].xpath('.//a')
            for curr_cinema in cinema_list:
                cinema_name = curr_cinema.xpath('./text()').extract_first()
                url = curr_cinema.xpath('./@href').extract_first()
                url = response.urljoin(url)
                request = scrapy.Request(url,
                                         callback=self.parse_cinema)
                request.meta['county_name'] = response.meta['county_name']
                request.meta['cinema_name'] = cinema_name
                # TEST
                cinema = Cinema()
                cinema['name'] = cinema_name
                cinema['county'] = response.meta['county_name']
                cinema['screens'] = {}
                yield cinema
                #yield request
                #return request

    def parse_cinema(self, response):
        print(response.meta['county_name'])
        print(response.meta['cinema_name'])
        cinema = Cinema()
        cinema['name'] = response.meta['cinema_name']
        cinema['county'] = response.meta['county_name']
        cinema['screens'] = self.parse_screen_data(response)

    def parse_screen_data(self, response):
        screen_raw_texts = response.xpath(
            '//th[text()="音響・設備"]/../..//td/text()').extract()
        screen = {}
        for raw_text in screen_raw_texts:
            raw_text = unicodedata.normalize('NFKC', raw_text)
            screen_name = re.sub(r"^(.+) (.+) (.+)", r"\1", raw_text)
            seat_count = re.sub(r"^(.+) (\d+)(.*) (.+)", r"\2", raw_text)
            print(screen_name)
            print(seat_count)
