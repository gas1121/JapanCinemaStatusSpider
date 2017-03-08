# -*- coding: utf-8 -*-
import re
import unicodedata
import scrapy
from scrapyproject.items import (Cinema, standardize_cinema_name,
                                 standardize_screen_name)
from scrapyproject.utils.spider_helper import CinemasDatabaseMixin
from scrapyproject.utils.site_utils import (standardize_county_name,
                                            extract_seat_number,
                                            standardize_site_url)


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
            county_name = standardize_county_name(county_name)
            # TEST
            if county_name != "兵庫県":
                continue
            url = county.xpath('./@href').extract_first()
            url = response.urljoin(url)
            request = scrapy.Request(url, callback=self.parse_county)
            request.meta['county_name'] = county_name
            yield request

    def parse_county(self, response):
        cinema_list = response.xpath('//div[@id="theater"]//a')
        for curr_cinema in cinema_list:
            cinema_name = curr_cinema.xpath('./text()').extract_first()
            cinema_name = standardize_cinema_name(cinema_name)
            url = curr_cinema.xpath('./@href').extract_first()
            url = response.urljoin(url) + "/info/"
            request = scrapy.Request(url, callback=self.parse_cinema)
            request.meta['county_name'] = response.meta['county_name']
            request.meta['cinema_name'] = cinema_name
            yield request

    def parse_cinema(self, response):
        cinema = Cinema()
        cinema['names'] = [response.meta['cinema_name']]
        cinema['county'] = response.meta['county_name']
        site = response.xpath(
            '//th[text()="公式サイト"]/..//a/text()').extract_first()
        if site:
            cinema['site'] = standardize_site_url(site, cinema)
        (cinema['screens'], cinema['screen_count'],
         cinema['total_seats']) = self.parse_screen_data(response, cinema)
        cinema['source'] = self.name
        yield cinema

    def parse_screen_data(self, response, cinema):
        screen_raw_texts = response.xpath(
            '//th[text()="座席"]/..//li/text()').extract()
        screen = {}
        screen_count = 0
        total_seats = 0
        pattern = re.compile(r"^\[?(.*?)[\] ]?客席数 (.+)$")
        for raw_text in screen_raw_texts:
            raw_text = unicodedata.normalize('NFKC', raw_text)
            if not pattern.match(raw_text):
                continue
            screen_name = pattern.sub(r"\1", raw_text)
            screen_name = standardize_screen_name(screen_name, cinema)
            # add cinema name into screen name to avoid conflict for
            # sub cinemas
            screen_name = response.meta['cinema_name'] + "#" + screen_name
            seat_str = pattern.sub(r"\2", raw_text)
            seat_count = extract_seat_number(seat_str)
            screen_count += 1
            total_seats += seat_count
            screen[screen_name] = str(seat_count)
        return screen, screen_count, total_seats
