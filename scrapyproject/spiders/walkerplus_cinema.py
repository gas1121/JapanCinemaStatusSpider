# -*- coding: utf-8 -*-
import scrapy
from scrapyproject.items import Cinema
from scrapyproject.utils.spider_helper import CinemasDatabaseMixin


class WalkerplusCinemaSpider(scrapy.Spider, CinemasDatabaseMixin):
    """
    spider to crawl cinema info from http://movie.walkerplus.com
    """
    name = "walkerplus_cinema"
    allowed_domains = ["movie.walkerplus.com"]
    start_urls = ['http://movie.walkerplus.com/theater/']

    def parse(self, response):
        """
        crawl cinema data from http://movie.walkerplus.com/theater/
        """
        county_list = response.xpath('//div[@id="rootAreaList"]//a')
        for county in county_list:
            county_name = county.xpath('.//text()').extract_first()
            if county_name in ['札幌', '道央', '道北', '道南', '道東']:
                continue
            url = county.xpath('./@href').extract_first()
            url = response.urljoin(url)
            request = scrapy.Request(url, callback=self.parse_county)
            request.meta['county_name'] = county_name
            yield request

    def parse_county(self, response):
        cinema_list = response.xpath('//div[@id="theaterList_wrap"]//li/a')
        for curr_cinema in cinema_list:
            cinema_name = curr_cinema.xpath('.//text()').extract_first()
            # TEST
            cinema = Cinema()
            cinema['name'] = cinema_name
            cinema['county'] = response.meta['county_name']
            cinema['screens'] = {}
            yield cinema
