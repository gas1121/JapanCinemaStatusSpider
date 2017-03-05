# -*- coding: utf-8 -*-
import scrapy
from scrapyproject.items import Cinema
from scrapyproject.utils.spider_helper import CinemasDatabaseMixin


class YahooCinemaSpider(scrapy.Spider, CinemasDatabaseMixin):
    """
    spider to crawl cinema info from http://movies.yahoo.co.jp
    """
    name = "yahoo_cinema"
    allowed_domains = ["movies.yahoo.co.jp"]
    start_urls = ['http://movies.yahoo.co.jp/area/']

    def parse(self, response):
        """
        crawl cinema data from http://movies.yahoo.co.jp/area/
        """
        county_list = response.xpath('//div[@id="allarea"]//a')
        for county in county_list:
            county_name = county.xpath('./text()').extract_first()
            url = county.xpath('./@href').extract_first()
            url = response.urljoin(url)
            request = scrapy.Request(url, callback=self.parse_county)
            request.meta['county_name'] = county_name
            yield request

    def parse_county(self, response):
        cinema_list = response.xpath('//div[@id="theater"]//a')
        for curr_cinema in cinema_list:
            cinema_name = curr_cinema.xpath('./text()').extract_first()
            # TEST
            cinema = Cinema()
            cinema['name'] = cinema_name
            cinema['county'] = response.meta['county_name']
            cinema['screens'] = {}
            yield cinema
