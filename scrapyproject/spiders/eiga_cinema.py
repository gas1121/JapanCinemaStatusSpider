# -*- coding: utf-8 -*-
import copy
import scrapy


class EigaCinemaSpider(scrapy.Spider):
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

    def parse_county(self, response):
        city_list = response.xpath('//div[@id="pref_theaters"]/h4')
        cinema_per_city_list = response.xpath('//div[@id="pref_theaters"]/ul')
        for i in range(len(city_list)):
            city_name = city_list[i].xpath('./text()').extract_first()
            cinema_list = cinema_per_city_list[i].xpath('.//a')
            for curr_cinema in cinema_list:
                cinema_name = curr_cinema.xpath('./text()').extract_first()
                url = curr_cinema.xpath('./@href').extract_first()
                url = response.urljoin(url)
                request = scrapy.Request(url,
                                         callback=self.parse_cinema)
                request.meta['area_name'] = response.meta['area_name']
                request.meta['county_name'] = response.meta['county_name']
                request.meta['city_name'] = city_name
                request.meta['cinema_name'] = cinema_name
                yield request

    def parse_cinema(self, response):
        print(response.meta['area_name'])
        print(response.meta['county_name'])
        print(response.meta['city_name'])
        print(response.meta['cinema_name'])
