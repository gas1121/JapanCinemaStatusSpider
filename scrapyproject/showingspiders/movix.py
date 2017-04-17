# -*- coding: utf-8 -*-
import re
import copy
import arrow
import scrapy
from scrapyproject.showingspiders.showing_spider import ShowingSpider
from scrapyproject.items import (ShowingItem, standardize_cinema_name,
                                 standardize_screen_name)
from scrapyproject.utils.site_utils import MovixUtil


class MovieSpider(ShowingSpider):
    """
    movix site spider.
    """
    name = "movix"
    allowed_domains = [
        'www.smt-cinema.com',
        'ticket.smt-cinema.com',
        'www.parkscinema.com',
        'ticket.parkscinema.com',
        'www.osakastationcitycinema.com',
        'ticket.osakastationcitycinema.com'
    ]
    start_urls = [
        'http://www.smt-cinema.com/theater/'
    ]

    cinema_list = ['新宿ピカデリー']

    def parse(self, response):
        """
        crawl theater list data first
        """
        theater_list = response.xpath('//div[@class="theater_info"]//li/a')
        for theater_element in theater_list:
            curr_cinema_url = theater_element.xpath(
                './@href').extract_first()
            cinema_name = theater_element.xpath('./text()').extract_first()
            if not cinema_name:
                # partner theater element is different
                cinema_name = ''.join(theater_element.xpath(
                    './/text()').extract())
            else:
                curr_cinema_url = response.urljoin(curr_cinema_url)
            cinema_name = standardize_cinema_name(cinema_name)
            if not self.is_cinema_crawl([cinema_name]):
                continue
            request = scrapy.Request(
                curr_cinema_url, callback=self.parse_cinema)
            request.meta["cinema_name"] = cinema_name
            request.meta["cinema_site"] = curr_cinema_url
            yield request

    def parse_cinema(self, response):
        """
        get cinema code from homepage's javascript
        """
        script_text = response.xpath(
            '//script[contains(.,"thnumber")]/text()').extract_first()
        thnumber = re.findall(r'\d+', script_text)[0]
        schedule_url = self.generate_cinema_schedule_url(
            response.url, thnumber, self.date)
        request = scrapy.Request(
            schedule_url, encoding='utf-8', callback=self.parse_shechedule)
        request.meta["cinema_name"] = response.meta["cinema_name"]
        request.meta["cinema_site"] = response.meta["cinema_site"]
        yield request

    def generate_cinema_schedule_url(self, site_url, thnumber, show_day):
        """
        schedule url for single cinema, all movies of curr cinema
        """
        main_url = re.findall(r'(http://.+/)site', site_url)[0]
        url = main_url + 'schedule/pc/s0100_{thnumber}_{show_day}.html'.format(
                  thnumber=thnumber, show_day=show_day)
        return url

    def parse_shechedule(self, response):
        data_proto = ShowingItem()
        data_proto['cinema_name'] = response.meta['cinema_name']
        data_proto["cinema_site"] = response.meta['cinema_site']
        data_proto['source'] = self.name
        result_list = []
        movie_section_list = response.xpath('//div[@class="scheduleBox"]')
        for curr_movie in movie_section_list:
            self.parse_movie(response, curr_movie, data_proto, result_list)
        for result in result_list:
            if result:
                yield result

    def parse_movie(self, response, curr_movie, data_proto, result_list):
        """
        parse movie showing data
        """
        title = curr_movie.xpath(
            './/div[@class="MovieTitle1"]//a/text()').extract_first()
        title_list = [title]
        if not self.is_movie_crawl(title_list):
            return
        movie_data_proto = copy.deepcopy(data_proto)
        movie_data_proto['title'] = title
        showing_section_list = curr_movie.xpath(
            './/td[contains(@onmouseover,"eventover")]')
        for curr_showing in showing_section_list:
            self.parse_showing(response, curr_showing,
                               movie_data_proto, result_list)

    def parse_showing(self, response, curr_showing, data_proto, result_list):
        def parse_time(time_str):
            time = time_str.split(":")
            return (int(time[0]), int(time[1]))

        showing_data_proto = copy.deepcopy(data_proto)
        screen_name = curr_showing.xpath('./p/text()').extract_first()
        showing_data_proto['screen'] = standardize_screen_name(
            screen_name, showing_data_proto['cinema_name'])
        start_time = curr_showing.xpath(
            './/span[@class="strong fontXL"]/text()').extract_first()
        start_hour, start_minute = parse_time(start_time)
        showing_data_proto['start_time'] = self.get_time_from_text(
            start_hour, start_minute)
        end_time = curr_showing.xpath(
            './/span[@class="strong fontXL"]/../text()').extract_first()[1:]
        end_hour, end_minute = parse_time(end_time)
        showing_data_proto['end_time'] = self.get_time_from_text(
            end_hour, end_minute)
        showing_data_proto['seat_type'] = 'NormalSeat'
        book_status = curr_showing.xpath('.//img/@src').extract_first()
        showing_data_proto['book_status'] = \
            MovixUtil.standardize_book_status(book_status)
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
            showing_script = curr_showing.xpath('./@onclick').extract_first()
            url = re.findall(r'\(\'(.+?)\'\,', showing_script)[0]
            request = scrapy.Request(url, callback=self.parse_normal_showing)
            request.meta["data_proto"] = showing_data_proto
            result_list.append(request)

    def parse_normal_showing(self, response):
        result = response.meta["data_proto"]
        booked_seat_count = len(response.xpath(
            '//img[contains(@src,"seat_no.gif")]'))
        result['book_seat_count'] = booked_seat_count
        result['record_time'] = arrow.now()
        yield result
