# -*- coding: utf-8 -*-
import copy
import arrow
import scrapy
from scrapyproject.showingspiders.showing_spider import ShowingSpider
from scrapyproject.items import (ShowingItem, ShowingBookingItem,
                                 standardize_cinema_name,
                                 standardize_screen_name)
from scrapyproject.utils import standardize_site_url, KinezoUtil


class KinezoSpider(ShowingSpider):
    """
    kinezo site spider.
    """
    name = "kinezo"
    allowed_domains = ['kinezo.jp']
    start_urls = [
        'http://kinezo.jp/pc/'
    ]
    # disallow concurrent requests to avoid cookie expiring
    custom_settings = {
        'CONCURRENT_REQUESTS': 1
    }

    cinema_list = ['新宿バルト9']

    def parse(self, response):
        """
        crawl theater list data first
        """
        theater_list = response.xpath(
            '//footer/p[position()>=2 and position() <=3]//a')
        # partner cinema is not included
        for theater_element in theater_list:
            curr_cinema_url = theater_element.xpath(
                './@href').extract_first()
            cinema_name = theater_element.xpath('./text()').extract_first()
            cinema_name = standardize_cinema_name(cinema_name)
            if not self.is_cinema_crawl([cinema_name]):
                continue
            cinema_name_en = curr_cinema_url.split('/')[-1].split('?')[0]
            request = scrapy.Request(
                curr_cinema_url, callback=self.parse_main_page)
            request.meta["cinema_name"] = cinema_name
            request.meta["cinema_site"] = curr_cinema_url
            request.meta["cinema_name_en"] = cinema_name_en
            request.meta["dont_merge_cookies"] = True
            yield request

    def parse_main_page(self, response):
        """
        cinema main page

        generate cookie here
        """
        cinema_name_en = response.meta["cinema_name_en"]
        schedule_url = self.generate_cinema_schedule_url(
            cinema_name_en, self.date)
        request = scrapy.Request(schedule_url, callback=self.parse_cinema)
        request.meta["cinema_name"] = response.meta["cinema_name"]
        request.meta["cinema_site"] = response.meta["cinema_site"]
        yield request

    def generate_cinema_schedule_url(self, cinema_name_en, show_day):
        """
        schedule url for single cinema, all movies of curr cinema
        """
        url = 'http://kinezo.jp/pc/{name}/schedule/index/{y}/{m}/{d}'.format(
                  name=cinema_name_en, y=show_day[:4], m=show_day[4:6],
                  d=show_day[6:])
        return url

    def parse_cinema(self, response):
        """
        cinema home page
        we have to pass this page to get independent cookie for each cinema
        """
        data_proto = ShowingItem()
        data_proto['cinema_name'] = response.meta['cinema_name']
        data_proto["cinema_site"] = response.meta['cinema_site']
        data_proto['source'] = self.name
        result_list = []
        movie_title_list = response.xpath('//div[@class="cinemaTitle elp"]')
        movie_section_list = response.xpath('//div[@class="theaterListWrap"]')
        for curr_movie in zip(movie_title_list, movie_section_list):
            self.parse_movie(response, curr_movie, data_proto, result_list)
        for result in result_list:
            if result:
                yield result

    def parse_movie(self, response, curr_movie, data_proto, result_list):
        """
        parse movie showing data

        curr_movie is a tuple
        """
        title_section, detail_section = curr_movie
        title = ''.join(title_section.xpath('./text()').extract())
        title = title.strip()
        title_list = [title]
        if not self.is_movie_crawl(title_list):
            return
        movie_data_proto = copy.deepcopy(data_proto)
        movie_data_proto['title'] = title
        screen_section_list = detail_section.xpath('.//table')
        for curr_screen in screen_section_list:
            self.parse_screen(response, curr_screen,
                              movie_data_proto, result_list)

    def parse_screen(self, response, curr_screen, data_proto, result_list):
        screen_data_proto = copy.deepcopy(data_proto)
        screen_name = curr_screen.xpath('./tr/td[1]/text()').extract_first()
        screen_data_proto['screen'] = standardize_screen_name(
            screen_name, screen_data_proto['cinema_name'])
        show_section_list = curr_screen.xpath('./tr/td[2]/a')
        for curr_showing in show_section_list:
            self.parse_showing(response, curr_showing,
                               screen_data_proto, result_list)

    def parse_showing(self, response, curr_showing, data_proto, result_list):
        showing_data_proto = copy.deepcopy(data_proto)
        start_time = curr_showing.xpath(
            './div/text()').extract_first()[:-1]
        start_hour, start_minute = self.parse_time(start_time)
        showing_data_proto['start_time'] = self.get_time_from_text(
            start_hour, start_minute)
        # end time not displayed in schedule page

        showing_data_proto['seat_type'] = 'NormalSeat'

        # query screen number from database
        showing_data_proto['total_seat_count'] = \
            self.get_screen_seat_count(showing_data_proto)
        # check whether need to continue crawl booking data or stop now
        if not self.crawl_booking_data:
            result_list.append(showing_data_proto)
            return

        booking_data_proto = ShowingBookingItem()
        booking_data_proto['showing'] = showing_data_proto
        book_status = curr_showing.xpath('./div/@class').extract_first()
        booking_data_proto['book_status'] = \
            KinezoUtil.standardize_book_status(book_status)
        if booking_data_proto['book_status'] in ['SoldOut', 'NotSold']:
            # sold out or not sold
            status = booking_data_proto['book_status']
            booking_data_proto['book_seat_count'] = (
                showing_data_proto['total_seat_count']
                if status == 'SoldOut' else 0)
            booking_data_proto['record_time'] = arrow.now()
            booking_data_proto['minutes_before'] = \
                self.get_minutes_before(booking_data_proto)
            result_list.append(booking_data_proto)
            return
        else:
            # normal, need to crawl book number on order page
            url = curr_showing.xpath('./@href').extract_first()
            url = response.urljoin(url)
            request = scrapy.Request(url, callback=self.parse_normal_showing)
            request.meta["data_proto"] = booking_data_proto
            result_list.append(request)

    def parse_normal_showing(self, response):
        result = response.meta["data_proto"]
        time_text = response.xpath(
            '//span[@class="screenTime"]/text()').extract_first()
        time_list = time_text.split('-')
        start_time = time_list[0].strip()
        start_hour, start_minute = self.parse_time(start_time)
        result['showing']['start_time'] = self.get_time_from_text(
            start_hour, start_minute)
        end_time = time_list[1].strip()
        end_hour, end_minute = self.parse_time(end_time)
        result['showing']['end_time'] = self.get_time_from_text(
            end_hour, end_minute)

        booked_seat_count = len(response.xpath(
            '//li[@class="seatSell seatOff"]'))
        result['book_seat_count'] = booked_seat_count
        result['record_time'] = arrow.now()
        result['minutes_before'] = self.get_minutes_before(result)
        yield result

    def parse_time(self, time_str):
        time = time_str.split(":")
        return (int(time[0]), int(time[1]))
