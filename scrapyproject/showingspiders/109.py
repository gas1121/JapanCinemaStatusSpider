# -*- coding: utf-8 -*-
import re
import copy
import arrow
import scrapy
from scrapyproject.showingspiders.showing_spider import ShowingSpider
from scrapyproject.items import (ShowingItem, standardize_cinema_name,
                                 standardize_screen_name)
from scrapyproject.utils import Site109Util


class Site109Spider(ShowingSpider):
    """
    109 site spider.
    """
    name = "site109"
    allowed_domains = ['109cinemas.net', 'cinema.109cinemas.net']
    start_urls = [
        'http://109cinemas.net/'
    ]

    cinema_list = ['109シネマズ湘南']

    def parse(self, response):
        """
        crawl theater list data first
        """
        theater_list = response.xpath('//section[@id="theatres"]//a')
        for theater_element in theater_list:
            curr_cinema_url = theater_element.xpath(
                './@href').extract_first()
            cinema_name = theater_element.xpath('./text()').extract_first()
            if cinema_name != "ムービル":
                cinema_name = "109シネマズ" + cinema_name
            cinema_name = standardize_cinema_name(cinema_name)
            if not self.is_cinema_crawl([cinema_name]):
                continue
            cinema_name_en = curr_cinema_url.split('/')[-2]
            schedule_url = self.generate_cinema_schedule_url(
                cinema_name_en, self.date)
            request = scrapy.Request(schedule_url, callback=self.parse_cinema)
            request.meta["cinema_name"] = cinema_name
            request.meta["cinema_site"] = response.urljoin(curr_cinema_url)
            yield request

    def generate_cinema_schedule_url(self, cinema_name_en, show_day):
        """
        schedule url for single cinema, all movies of curr cinema
        """
        url = 'http://109cinemas.net/{cinema_name_en}/schedules/{date}.html'\
              '/daily.php?date={date}'.format(
                  cinema_name_en=cinema_name_en, date=show_day)
        return url

    def parse_cinema(self, response):
        data_proto = ShowingItem()
        data_proto['cinema_name'] = response.meta['cinema_name']
        data_proto["cinema_site"] = response.meta['cinema_site']
        result_list = []
        movie_section_list = response.xpath('//div[@id="timetable"]/article')
        for curr_movie in movie_section_list:
            self.parse_movie(response, curr_movie, data_proto, result_list)
        for result in result_list:
            if result:
                yield result

    def parse_movie(self, response, curr_movie, data_proto, result_list):
        """
        parse movie showing data
        """
        title = curr_movie.xpath('./header/a/h2/text()').extract_first()
        title_en = curr_movie.xpath('./header/a/p/text()').extract_first()
        title_list = [title, title_en]
        if not self.is_movie_crawl(title_list):
            return
        movie_data_proto = copy.deepcopy(data_proto)
        movie_data_proto['title'] = title
        movie_data_proto['title_en'] = title_en
        screen_section_list = curr_movie.xpath('./ul')
        for curr_screen in screen_section_list:
            self.parse_screen(response, curr_screen,
                              movie_data_proto, result_list)

    def parse_screen(self, response, curr_screen, data_proto, result_list):
        screen_data_proto = copy.deepcopy(data_proto)
        screen_name = ''.join(curr_screen.xpath(
            './li[@class="theatre"]/a//text()').extract())
        screen_data_proto['screen'] = standardize_screen_name(
            screen_name, screen_data_proto['cinema_name'])
        show_section_list = curr_screen.xpath('./li')[1:]
        for curr_showing in show_section_list:
            self.parse_showing(response, curr_showing,
                               screen_data_proto, result_list)

    def parse_showing(self, response, curr_showing, data_proto, result_list):
        def parse_time(time_str):
            time = time_str.split(":")
            return (int(time[0]), int(time[1]))

        showing_data_proto = copy.deepcopy(data_proto)
        start_time = curr_showing.xpath(
            './/time[@class="start"]/text()').extract_first()
        start_hour, start_minute = parse_time(start_time)
        showing_data_proto['start_time'] = self.get_time_from_text(
            start_hour, start_minute)
        end_time = curr_showing.xpath(
            './/time[@class="end"]/text()').extract_first()
        end_hour, end_minute = parse_time(end_time)
        showing_data_proto['end_time'] = self.get_time_from_text(
            end_hour, end_minute)
        showing_data_proto['seat_type'] = 'NormalSeat'
        book_status = curr_showing.xpath(
            './a/div/@class').extract_first()
        showing_data_proto['book_status'] = \
            Site109Util.standardize_book_status(book_status)
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
            url = curr_showing.xpath('./a/@href').extract_first()
            request = scrapy.Request(url, callback=self.parse_normal_showing)
            request.meta["data_proto"] = showing_data_proto
            result_list.append(request)

    def parse_normal_showing(self, response):
        """
        parse seat order page
        """
        # extract seat json api from javascript
        script_text = response.xpath(
            '//script[contains(.,"get seatmap data")]/text()').extract_first()
        post_json_data = re.findall(r'ajax\(({.+resv_screen_ppt.+?})\)',
                                    script_text, re.DOTALL)[0]
        post_json_data = re.sub('\s+', '', post_json_data)
        url = re.findall(r'url:\'(.+?)\'', post_json_data)[0]
        crt = re.findall(r'crt:\'(.+?)\'', post_json_data)[0]
        konyu_su = re.findall(r'konyu_su:\'(.+?)\'', post_json_data)[0]
        url = (url + '?crt=' + crt + '&konyu_su=' + konyu_su + '&mit=')
        request = scrapy.Request(url, method='POST',
                                 callback=self.parse_seat_json_api)
        request.meta["data_proto"] = response.meta['data_proto']
        yield request

    def parse_seat_json_api(self, response):
        result = response.meta["data_proto"]
        empty_normal_seat_count = len(response.xpath(
            '//a[@class="seat seat-empty"]'))
        empty_wheelseat_count = len(response.xpath(
            '//a[@class="seat wheelseat-empty"]'))
        empty_executive_seat_count = len(response.xpath(
            '//a[@class="seat executive-empty"]'))
        booked_normal_seat_count = len(response.xpath(
            '//a[@class="seat seat-none"]'))
        booked_wheelseat_count = len(response.xpath(
            '//a[@class="seat wheelseat-none"]'))
        booked_executive_seat_count = len(response.xpath(
            '//a[@class="seat executive-none"]'))
        booked_seat_count = (
            booked_normal_seat_count + booked_wheelseat_count +
            booked_executive_seat_count)
        empty_seat_count = (
            empty_normal_seat_count + empty_wheelseat_count +
            empty_executive_seat_count)
        result['book_seat_count'] = booked_seat_count
        result['total_seat_count'] = (empty_seat_count + booked_seat_count)
        result['record_time'] = arrow.now()
        result['source'] = self.name
        yield result
