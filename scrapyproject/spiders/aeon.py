# -*- coding: utf-8 -*-
import re
import unicodedata
import copy
import arrow
import scrapy
from scrapyproject.spiders.showing_spider import ShowingSpider
from scrapyproject.items import (Showing, standardize_cinema_name,
                                 standardize_screen_name)
from scrapyproject.utils.site_utils import AeonUtil


class AeonSpider(ShowingSpider):
    """
    aeon spider.
    """
    name = "aeon"
    allowed_domains = ["www.aeoncinema.com", "cinema.aeoncinema.com"]
    start_urls = [
        'http://www.aeoncinema.com/theater/'
    ]

    cinema_list = ['イオンシネマ板橋']

    def parse(self, response):
        """
        crawl theater list data first
        """
        theater_link_list = response.xpath(
            '//div[@class="bot clearfix"]//a')
        for theater_link in theater_link_list:
            # forum site have multiple cinema on one site, so we need to
            # specify cinema name on schedule page
            city_name = theater_link.xpath('./text()').extract_first()
            cinema_name = "イオンシネマ"+city_name
            standardize_cinema_name(cinema_name)
            if not self.is_cinema_crawl([cinema_name]):
                continue
            curr_cinema_url = theater_link.xpath('./@href').extract_first()
            curr_cinema_url = response.urljoin(curr_cinema_url)
            request = scrapy.Request(curr_cinema_url,
                                     callback=self.parse_cinema)
            request.meta["cinema_name"] = cinema_name
            request.meta["cinema_site"] = curr_cinema_url
            yield request

    def parse_cinema(self, response):
        """
        get schedule page from cinema site
        """
        schedule_url = response.xpath(
            '//a[contains(@href,"' + self.date + '")]/@href').extract_first()
        request = scrapy.Request(schedule_url,
                                 callback=self.parse_cinema_schedule)
        request.meta["cinema_name"] = response.meta['cinema_name']
        request.meta["cinema_site"] = response.meta['cinema_site']
        yield request

    def parse_cinema_schedule(self, response):
        data_proto = Showing()
        data_proto['cinema_name'] = response.meta['cinema_name']
        data_proto["cinema_site"] = response.meta['cinema_site']
        result_list = []
        movie_section_list = response.xpath(
            '//div[contains(@class,"movielist")]')
        for curr_movie in movie_section_list:
            self.parse_movie(response, curr_movie, data_proto, result_list)
        for result in result_list:
            if result:
                yield result

    def parse_movie(self, response, curr_movie, data_proto, result_list):
        """
        parse movie showing data
        """
        return
        title = curr_movie.xpath('./div[1]/p[1]/a[1]/text()').extract_first()
        title = title.strip()
        title_en = curr_movie.xpath(
            './div[1]/p[1]/span/text()').extract_first()
        title_list = [title, title_en]
        if not self.is_movie_crawl(title_list):
            return
        movie_data_proto = copy.deepcopy(data_proto)
        movie_data_proto['title'] = title
        movie_data_proto['title_en'] = title_en
        show_section_list = curr_movie.xpath(
            './div[2]/div')
        for curr_showing in show_section_list:
            self.parse_showing(response, curr_showing,
                               movie_data_proto, result_list)

    def parse_showing(self, response, curr_showing, data_proto, result_list):
        def parse_time(time_str):
            time = time_str.split(":")
            return (int(time[0]), int(time[1]))

        # showing section passed in may be unusable and need to be filtered
        time_section = curr_showing.xpath('./div[@class="time"]')
        if not time_section:
            return
        showing_data_proto = copy.deepcopy(data_proto)
        start_time = time_section.xpath('./span/span/text()').extract_first()
        start_time = unicodedata.normalize('NFKC', start_time)
        start_hour, start_minute = parse_time(start_time)
        showing_data_proto['start_time'] = self.get_time_from_text(
            start_hour, start_minute)
        end_time = time_section.xpath('./span/text()').extract_first()
        end_time = unicodedata.normalize('NFKC', end_time)[1:]
        end_hour, end_minute = parse_time(end_time)
        showing_data_proto['end_time'] = self.get_time_from_text(
            end_hour, end_minute)
        screen_name = curr_showing.xpath('./div[@class="screen"]/a/text()')
        showing_data_proto['screen'] = screen_name
        book_status = curr_showing.xpath('./a/span/@class').extract_first()
        showing_data_proto['book_status'] = \
            AeonUtil.standardize_book_status(book_status)
        if showing_data_proto['book_status'] in ['SoldOut', 'NotSold']:
            # sold out or not sold, seat set to 0
            showing_data_proto['book_seat_count'] = 0
            showing_data_proto['total_seat_count'] = 0
            showing_data_proto['record_time'] = arrow.now()
            showing_data_proto['source'] = self.name
            result_list.append(showing_data_proto)
            return
        else:
            # TODO
            return
            # normal, need to crawl book number on order page
            url = curr_showing.xpath(
                './span[@class="purchase-block"]/a/@href').extract_first()
            request = scrapy.Request(url, callback=self.parse_normal_showing)
            request.meta["data_proto"] = showing_data_proto
            result_list.append(request)

    def parse_normal_showing(self, response):
        result = response.meta["data_proto"]
        info_block = response.xpath(
            '//div[@class="reservationstatus-inner accordion_mobile_inner"]'
            )
        screen_name = info_block.xpath('./div[2]/span/text()').extract_first()
        result['screen'] = standardize_screen_name(
            screen_name, result['cinema_name'])
        # extract seat info from javascript
        script_text = response.xpath(
            '//script[contains(., "seat_info")]/text()').extract_first()
        m = re.search(r'"total_seats":"(\d+)"', script_text)
        total_seat_count = int(m.group(1))
        m = re.search(r'"unsold_seat_number":"(\d+)"', script_text)
        unsold_seat_count = int(m.group(1))
        result['book_seat_count'] = total_seat_count - unsold_seat_count
        result['total_seat_count'] = total_seat_count
        result['record_time'] = arrow.now()
        result['source'] = self.name
        yield result
