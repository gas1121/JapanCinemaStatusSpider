# -*- coding: utf-8 -*-
import re
import unicodedata
import scrapy
from scrapyproject.items import Cinema
from scrapyproject.utils.spider_helper import CinemasDatabaseMixin
from scrapyproject.utils.site_utils import standardize_county_name
import requests


class EigaCinemaSpider(scrapy.Spider, CinemasDatabaseMixin):
    """
    crawl cinema info from http://eiga.com
    """
    name = "eiga_cinema"
    allowed_domains = ["eiga.com"]
    start_urls = ['http://eiga.com/theater/']

    def parse(self, response):
        """
        crawl cinema data from http://eiga.com/theater/
        """
        county_list = response.xpath('//dl[@id="list_b"]//a')
        for county in county_list:
            county_name = county.xpath('.//text()').extract_first()
            county_name = standardize_county_name(county_name)
            url = county.xpath('./@href').extract_first()
            url = response.urljoin(url)
            request = scrapy.Request(url, callback=self.parse_county)
            request.meta['county_name'] = county_name
            yield request

    def parse_county(self, response):
        cinema_list = response.xpath('//div[@id="pref_theaters"]//a')
        for curr_cinema in cinema_list:
            cinema_name = curr_cinema.xpath('./text()').extract_first()
            url = curr_cinema.xpath('./@href').extract_first()
            url = response.urljoin(url)
            request = scrapy.Request(url, callback=self.parse_cinema)
            request.meta['county_name'] = response.meta['county_name']
            request.meta['cinema_name'] = cinema_name
            yield request

    def parse_cinema(self, response):
        cinema = Cinema()
        cinema['names'] = [response.meta['cinema_name']]
        cinema['county'] = response.meta['county_name']
        site = response.xpath('//span[@id="official"]/a/@href').extract_first()
        site = response.urljoin(site)
        # we have to get redirected url
        if site:
            r = requests.get(site, allow_redirects=False)
            cinema['site'] = r.headers['Location']
        (cinema['screens'], cinema['screen_count'],
         cinema['total_seats']) = self.parse_screen_data(response)
        yield cinema

    def parse_screen_data(self, response):
        screen_raw_texts = response.xpath(
            '//th[text()="音響・設備"]/../..//td/text()').extract()
        screen = {}
        screen_count = 0
        total_seats = 0
        for raw_text in screen_raw_texts:
            raw_text = unicodedata.normalize('NFKC', raw_text)
            if "座席" not in raw_text:
                continue
            screen_name = re.sub(r"^(.+)  (.*)", r"\1", raw_text)
            screen_name = screen_name.strip()
            seat_count = re.sub(r"^(.+?)  (\d+)(.*)", r"\2", raw_text)
            screen_count += 1
            total_seats += int(seat_count)
            screen[screen_name] = seat_count
        return screen, screen_count, total_seats
