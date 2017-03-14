# -*- coding: utf-8 -*-
import unicodedata
import json
import copy
import arrow
import scrapy
from scrapyproject.spiders.showing_spider import ShowingSpider
from scrapyproject.items import (Showing, standardize_cinema_name,
                                 standardize_screen_name)
from scrapyproject.utils.site_utils import CinemaSunshineUtil


class CinemaSunshineSpider(ShowingSpider):
    """
    Cinema Sunshine spider.
    """
    name = "cinemasunshine"
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
            curr_cinema_url = theater_element.xpath(
                './p[@class="theaterName"]/a/@href').extract_first()
            cinema_name_en = curr_cinema_url.split('/')[-1]
            curr_cinema_url = self.generate_cinema_schedule_url(
                cinema_name_en, self.date)
            request = scrapy.Request(curr_cinema_url,
                                     callback=self.parse_cinema)
            request.meta["cinema_name"] = cinema_name
            request.meta["cinema_site"] = response.urljoin(curr_cinema_url)
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
        if 'data' not in schedule_data or 'movie' not in schedule_data['data']:
            return
        data_proto = Showing()
        data_proto['cinema_name'] = response.meta['cinema_name']
        data_proto["cinema_site"] = response.meta['cinema_site']
        result_list = []
        movie_list = []
        if isinstance(schedule_data['data']['movie'], dict):
            movie_list.append(schedule_data['data']['movie'])
        else:
            movie_list = schedule_data['data']['movie']
        for curr_movie in movie_list:
            self.parse_movie(response, curr_movie, data_proto, result_list)
        for result in result_list:
            if result:
                yield result

    def parse_movie(self, response, curr_movie, data_proto, result_list):
        """
        parse movie showing data
        """
        title = curr_movie['name']
        if not self.is_movie_crawl([title]):
            return
        movie_data_proto = copy.deepcopy(data_proto)
        movie_data_proto['title'] = title
        screen_list = []
        if isinstance(curr_movie['screen'], dict):
            screen_list.append(curr_movie['screen'])
        else:
            screen_list = curr_movie['screen']
        for curr_screen in screen_list:
            self.parse_screen(response, curr_screen, data_proto, result_list)

    def parse_screen(self, response, curr_screen, data_proto, result_list):
        screen = curr_screen['name']
        screen_data_proto = copy.deepcopy(data_proto)
        # make sure screen name is same with those in cinemas table
        screen_data_proto['screen'] = standardize_screen_name(
            screen, screen_data_proto['cinema_name'])
        showing_list = []
        if isinstance(curr_screen['time'], dict):
            showing_list.append(curr_screen['time'])
        else:
            showing_list = curr_screen['time']
        for curr_showing in showing_list:
            self.parse_showing(response, curr_showing, data_proto, result_list)

    def parse_showing(self, response, curr_showing, data_proto, result_list):
        def parse_time(time_str):
            return (int(time_str[:2]), int(time_str[2:]))
        showing_data_proto = copy.deepcopy(data_proto)
        start_hour, start_minute = parse_time(curr_showing['start_time'])
        showing_data_proto['start_time'] = self.get_time_from_text(
            start_hour, start_minute)
        end_hour, end_minute = parse_time(curr_showing['end_time'])
        showing_data_proto['end_time'] = self.get_time_from_text(
            end_hour, end_minute)
        showing_data_proto['book_status'] = \
            CinemaSunshineUtil.standardize_book_status(
                curr_showing['available'])
        if showing_data_proto['book_status'] in ['SoldOut', 'NotSold']:
            # sold out or not sold, seat set to 0
            showing_data_proto['book_seat_count'] = 0
            showing_data_proto['total_seat_count'] = 0
            showing_data_proto['record_time'] = arrow.now()
            showing_data_proto['source'] = self.name
            result_list.append(showing_data_proto)
            return
        else:
            # normal, need to crawl book number on order page
            url = curr_showing['url']
            request = scrapy.Request(url,
                                     callback=self.parse_normal_showing)
            request.meta["data_proto"] = showing_data_proto
            result_list.append(request)

    def parse_normal_showing(self, response):
        print(response.text)
