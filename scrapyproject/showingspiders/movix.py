# -*- coding: utf-8 -*-
import re
import scrapy
from scrapyproject.showingspiders.showing_spider import ShowingSpider
from scrapyproject.items import (ShowingLoader, ShowingBookingLoader)
from scrapyproject.utils import MovixUtil


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
            data_proto = ShowingLoader(response=response)
            data_proto.add_cinema_name(cinema_name)
            cinema_name = data_proto.get_output_value('cinema_name')
            data_proto.add_cinema_site(curr_cinema_url, cinema_name)
            data_proto.add_value('source', self.name)
            if not self.is_cinema_crawl([cinema_name]):
                continue
            request = scrapy.Request(
                curr_cinema_url, callback=self.parse_cinema)
            request.meta["data_proto"] = data_proto
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
        request.meta["data_proto"] = response.meta["data_proto"]
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
        data_proto = ShowingLoader(response=response)
        data_proto.add_value(None, response.meta["data_proto"].load_item())
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
        movie_data_proto = ShowingLoader(response=response)
        movie_data_proto.add_value(None, data_proto.load_item())
        movie_data_proto.add_title(title=title)
        title_list = movie_data_proto.get_title_list()
        if not self.is_movie_crawl(title_list):
            return
        showing_section_list = curr_movie.xpath(
            './/td[contains(@onmouseover,"eventover")]')
        for curr_showing in showing_section_list:
            self.parse_showing(response, curr_showing,
                               movie_data_proto, result_list)

    def parse_showing(self, response, curr_showing, data_proto, result_list):
        def parse_time(time_str):
            time = time_str.split(":")
            return (int(time[0]), int(time[1]))

        showing_data_proto = ShowingLoader(response=response)
        showing_data_proto.add_value(None, data_proto.load_item())
        screen_name = curr_showing.xpath('./p/text()').extract_first()
        showing_data_proto.add_screen_name(screen_name)
        start_time = curr_showing.xpath(
            './/span[@class="strong fontXL"]/text()').extract_first()
        start_hour, start_minute = parse_time(start_time)
        showing_data_proto.add_value('start_time', self.get_time_from_text(
            start_hour, start_minute))
        end_time = curr_showing.xpath(
            './/span[@class="strong fontXL"]/../text()').extract_first()[1:]
        end_hour, end_minute = parse_time(end_time)
        showing_data_proto.add_value('end_time', self.get_time_from_text(
            end_hour, end_minute))
        showing_data_proto.add_value('seat_type', 'NormalSeat')

        # query screen number from database
        showing_data_proto.add_total_seat_count()
        # check whether need to continue crawl booking data or stop now
        if not self.crawl_booking_data:
            result_list.append(showing_data_proto.load_item())
            return

        booking_data_proto = ShowingBookingLoader(response=response)
        booking_data_proto.context['util'] = MovixUtil
        booking_data_proto.context['loader'] = booking_data_proto
        booking_data_proto.add_value('showing', showing_data_proto.load_item())
        book_status = curr_showing.xpath('.//img/@src').extract_first()
        booking_data_proto.add_value('book_status', book_status)
        book_status = booking_data_proto.get_output_value('book_status')
        if book_status in ['SoldOut', 'NotSold']:
            # sold out or not sold
            total_seat_count = showing_data_proto.get_output_value(
                'total_seat_count')
            book_seat_count = (
                total_seat_count if book_status == 'SoldOut' else 0)
            booking_data_proto.add_value('book_seat_count', book_seat_count)
            booking_data_proto.add_time_data()
            result_list.append(booking_data_proto.load_item())
            return
        else:
            # normal, need to crawl book number on order page
            showing_script = curr_showing.xpath('./@onclick').extract_first()
            url = re.findall(r'\(\'(.+?)\'\,', showing_script)[0]
            request = scrapy.Request(url, callback=self.parse_normal_showing)
            request.meta["data_proto"] = booking_data_proto
            result_list.append(request)

    def parse_normal_showing(self, response):
        result = response.meta["data_proto"]
        booked_seat_count = len(response.xpath(
            '//img[contains(@src,"seat_no.gif")]'))
        result.add_value('book_seat_count', booked_seat_count)
        result.add_time_data()
        yield result.load_item()
