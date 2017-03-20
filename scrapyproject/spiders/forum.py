# -*- coding: utf-8 -*-
import re
import copy
import arrow
import scrapy
from scrapyproject.spiders.showing_spider import ShowingSpider
from scrapyproject.items import (Showing, standardize_cinema_name,
                                 standardize_screen_name)
from scrapyproject.utils.site_utils import ForumUtil


class ForumSpider(ShowingSpider):
    """
    forum spider.
    """
    name = "forum"
    start_urls = [
        'http://forum-movie.net/theater-list'
    ]

    cinema_list = ['フォーラム八戸']

    def parse(self, response):
        """
        crawl theater list data first
        """
        theater_div_list = response.xpath(
            '//div[@class="theater-list__inner"]')
        for theater_element in theater_div_list:
            # forum site have multiple cinema on one site, so we need to
            # specify cinema name on schedule page
            cinema_name = theater_element.xpath('./h4/text()').extract_first()
            standardize_cinema_name(cinema_name)
            if not self.is_cinema_crawl([cinema_name]):
                continue
            curr_cinema_url = theater_element.xpath(
                './p/a/@href').extract_first()
            schedule_url = self.generate_cinema_schedule_url(
                curr_cinema_url, self.date)
            request = scrapy.Request(schedule_url, callback=self.parse_cinema)
            request.meta["cinema_name"] = cinema_name
            request.meta["cinema_site"] = response.urljoin(curr_cinema_url)
            yield request

    def generate_cinema_schedule_url(self, curr_cinema_url, date):
        """
        schedule data url for single cinema, all movies of curr cinema
        """
        url = curr_cinema_url + "/by-date?date={date}".format(date=date)
        return url

    def parse_cinema(self, response):
        data_proto = Showing()
        data_proto['cinema_name'] = response.meta['cinema_name']
        data_proto["cinema_site"] = response.meta['cinema_site']
        result_list = []
        movie_section_list = response.xpath(
            '//section[@data-accordion-group="movie"]')
        for curr_movie in movie_section_list:
            self.parse_movie(response, curr_movie, data_proto, result_list)
        for result in result_list:
            if result:
                yield result

    def parse_movie(self, response, curr_movie, data_proto, result_list):
        """
        parse movie showing data
        """
        title = curr_movie.xpath('./h2/text()').extract_first()
        title_en = curr_movie.xpath('./h2/span/text()').extract_first()
        title_list = [title]
        if title_en:
            title_list.append(title_en)
        if not self.is_movie_crawl(title_list):
            return
        movie_data_proto = copy.deepcopy(data_proto)
        movie_data_proto['title'] = title
        if title_en:
            movie_data_proto['title_en'] = title_en
        show_section_list = curr_movie.xpath(
            './/ul[@class="timetable"]/li')
        for curr_showing in show_section_list:
            self.parse_showing(response, curr_showing,
                               movie_data_proto, result_list)

    def parse_showing(self, response, curr_showing, data_proto, result_list):
        def parse_time(time_str):
            time = time_str.split(":")
            return (int(time[0]), int(time[1]))

        showing_data_proto = copy.deepcopy(data_proto)
        start_time = curr_showing.xpath(
            './span[@class="start-time digit"]/text()').extract_first()
        start_hour, start_minute = parse_time(start_time)
        showing_data_proto['start_time'] = self.get_time_from_text(
            start_hour, start_minute)
        end_time = curr_showing.xpath(
            './span[@class="end-time digit"]/text()').extract_first()
        end_hour, end_minute = parse_time(end_time)
        showing_data_proto['end_time'] = self.get_time_from_text(
            end_hour, end_minute)
        cinema_name = curr_showing.xpath(
            './span[@class="movie-info-theater"]/text()').extract_first()
        # if extract cinema name from showing info, use this one
        if cinema_name:
            standardize_cinema_name(cinema_name)
            showing_data_proto['cinema_name'] = cinema_name
        book_status = curr_showing.xpath(
            './span[@class="purchase-block"]/a/@class').extract_first()
        showing_data_proto['book_status'] = \
            ForumUtil.standardize_book_status(book_status)
        if showing_data_proto['book_status'] in ['SoldOut', 'NotSold']:
            # CANNOTSOLVE we cannot get screen name from site for
            # sold out and not sold showings so we have to give it a special
            # screen name
            showing_data_proto['screen'] = "unknown"
            # sold out or not sold, seat set to 0
            showing_data_proto['book_seat_count'] = 0
            showing_data_proto['total_seat_count'] = 0
            showing_data_proto['record_time'] = arrow.now()
            showing_data_proto['source'] = self.name
            result_list.append(showing_data_proto)
            return
        else:
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
