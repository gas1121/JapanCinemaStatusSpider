# -*- coding: utf-8 -*-
import re
from crawler.showingspiders.showing_spider import ShowingSpider
from crawler.items import (ShowingLoader, ShowingBookingLoader,
                           init_show_booking_loader)
from crawler.utils import MovixUtil


class MovixSpider(ShowingSpider):
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
    """
    start_urls = [
        'http://www.smt-cinema.com/theater/'
    ]
    """

    def parse_first_page(self, response, result_list):
        """
        crawl theater list data first
        """
        self._logger.debug("{} parse_first_page".format(self.name))
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
            request = response.follow(curr_cinema_url, callback=self.parse)
            self.set_next_func(request, self.parse_cinema)
            request.meta["dict_proto"] = dict(data_proto.load_item())
            result_list.append(request)

    def parse_cinema(self, response, result_list):
        """
        get cinema code from homepage's javascript
        """
        self._logger.debug("{} parse_cinema".format(self.name))
        script_text = response.xpath(
            '//script[contains(.,"thnumber")]/text()').extract_first()
        thnumber = re.findall(r'\d+', script_text)[0]
        schedule_url = self.generate_cinema_schedule_url(
            response.url, thnumber, self.date)
        request = response.follow(
            schedule_url, encoding='utf-8', callback=self.parse)
        self.set_next_func(request, self.parse_schedule)
        request.meta["dict_proto"] = response.meta["dict_proto"]
        result_list.append(request)

    def generate_cinema_schedule_url(self, site_url, thnumber, show_day):
        """
        schedule url for single cinema, all movies of curr cinema
        """
        main_url = re.findall(r'(http://.+/)site', site_url)[0]
        url = main_url + 'schedule/pc/s0100_{thnumber}_{show_day}.html'.format(
                  thnumber=thnumber, show_day=show_day)
        return url

    def parse_schedule(self, response, result_list):
        self._logger.debug("{} parse_schedule".format(self.name))
        data_proto = ShowingLoader(response=response)
        data_proto.add_value(None, response.meta["dict_proto"])
        movie_section_list = response.xpath('//div[@class="scheduleBox"]')
        for curr_movie in movie_section_list:
            self.parse_movie(response, curr_movie, data_proto, result_list)

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

        # check whether need to continue crawl booking data or stop now
        if not self.crawl_booking_data:
            result_list.append(showing_data_proto.load_item())
            return

        booking_data_proto = init_show_booking_loader(response=response)
        booking_data_proto.add_value('showing', showing_data_proto.load_item())
        book_status = curr_showing.xpath('.//img/@src').extract_first()
        booking_data_proto.add_book_status(book_status, util=MovixUtil)
        book_status = booking_data_proto.get_output_value('book_status')
        if book_status in ['SoldOut', 'NotSold']:
            # sold out or not sold, set book_seat_count to 0 temporarily
            booking_data_proto.add_value('book_seat_count', 0)
            booking_data_proto.add_time_data()
            result_list.append(booking_data_proto.load_item())
        else:
            # normal, need to crawl book number on order page
            showing_script = curr_showing.xpath('./@onclick').extract_first()
            url = re.findall(r'\(\'(.+?)\'\,', showing_script)[0]
            request = response.follow(url, callback=self.parse)
            dict_proto = ShowingBookingLoader.to_dict(
                booking_data_proto.load_item())
            self.set_next_func(request, self.parse_normal_showing)
            request.meta["dict_proto"] = dict_proto
            result_list.append(request)

    def parse_normal_showing(self, response, result_list):
        self._logger.debug("{} parse_normal_showing".format(self.name))
        result = init_show_booking_loader(
            response=response, item=response.meta["dict_proto"])
        booked_seat_count = len(response.xpath(
            '//img[contains(@src,"seat_no.gif")]'))
        result.add_value('book_seat_count', booked_seat_count)
        result.add_time_data()
        result_list.append(result.load_item())
