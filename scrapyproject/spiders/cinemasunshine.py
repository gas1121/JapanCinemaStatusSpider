# -*- coding: utf-8 -*-
import unicodedata
import json
import copy
import arrow
import scrapy
from scrapyproject.spiders.showing_spider import ShowingSpider
from scrapyproject.items import (Showing, standardize_cinema_name,
                                 standardize_screen_name)
from scrapyproject.utils.site_utils import standardize_book_status


class CinemaSunshineSpider(ShowingSpider):
    """
    Cinema Sunshine spider.
    """
    name = "cinemasunshine"
    allowed_domains = ["www.cinemasunshine.co.jp", "www2.css-ebox.jp"]
    start_urls = [
        'http://www.cinemasunshine.co.jp/theater/'
    ]

    cinema_list = ['シネマサンシャイン池袋']

    def parse(self, response):
        """
        crawl theater list data first
        """
        theater_list = response.xpath('//li[@class="clearfix"]')
        for theater_element in theater_list:
            cinema_name = theater_element.xpath(
                './p[@class="theaterName"]/a/text()').extract_first()
            if not self.is_cinema_crawl([cinema_name]):
                continue
            county = theater_element.xpath(
                './p[@class="theaterPracce"]/text()').extract_first()
            curr_cinema_url = theater_element.xpath(
                './p[@class="theaterName"]/a/@href').extract_first()
            cinema_name_en = curr_cinema_url.split('/')[-1]
            curr_cinema_url = self.generate_cinema_schedule_url(
                cinema_name_en, self.date)
            request = scrapy.Request(curr_cinema_url,
                                     callback=self.parse_cinema)
            request.meta["county"] = county
            #yield request
            return request

    def generate_cinema_schedule_url(self, cinema_name, date):
        """
        json data url for single cinema, all movies of curr cinema
        """
        url = 'http://www.cinemasunshine.co.jp/lib/getJson.php?'\
              'theater={cinema_name}&date={date}&top=true'.format(
                cinema_name=cinema_name, date=date)
        return url

    def parse_cinema(self, response):
        try:
            schedule_data = json.loads(response.text)
        except json.JSONDecodeError:
            return
        if (not schedule_data):
            return
        print(schedule_data)
