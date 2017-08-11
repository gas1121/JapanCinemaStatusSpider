# -*- coding: utf-8 -*-
import re
from crawler.showingspiders.showing_spider import ShowingSpider
from crawler.items import (ShowingLoader, ShowingBookingLoader,
                           init_show_booking_loader)
from crawler.utils import ForumUtil


class ForumSpider(ShowingSpider):
    """
    forum spider.
    """
    name = "forum"
    """
    start_urls = [
        'http://forum-movie.net/theater-list'
    ]
    """

    def parse_first_page(self, response, result_list):
        """
        crawl theater list data first
        """
        # TODO bug after for each showing url not added but not crawled
        self._logger.debug("{} parse_first_page".format(self.name))
        theater_div_list = response.xpath(
            '//div[@class="theater-list__inner"]')
        for theater_element in theater_div_list:
            # forum site have multiple cinema on one site, so we need to
            # specify cinema name on schedule page
            cinema_name = theater_element.xpath('./h4/text()').extract_first()
            data_proto = ShowingLoader(response=response)
            data_proto.add_cinema_name(cinema_name)
            cinema_name = data_proto.get_output_value('cinema_name')
            if not self.is_cinema_crawl([cinema_name]):
                continue
            curr_cinema_url = theater_element.xpath(
                './p/a/@href').extract_first()
            data_proto.add_cinema_site(
                response.urljoin(curr_cinema_url), cinema_name)
            data_proto.add_value('source', self.name)
            schedule_url = self.generate_cinema_schedule_url(
                curr_cinema_url, self.loaded_config['date'])
            request = response.follow(schedule_url, callback=self.parse)
            self.set_next_func(request, self.parse_cinema)
            request.meta["dict_proto"] = dict(data_proto.load_item())
            result_list.append(request)

    def generate_cinema_schedule_url(self, curr_cinema_url, date):
        """
        schedule data url for single cinema, all movies of curr cinema
        """
        url = curr_cinema_url + "/by-date?date={date}".format(date=date)
        return url

    def parse_cinema(self, response, result_list):
        self._logger.debug("{} parse_cinema".format(self.name))
        data_proto = ShowingLoader(response=response)
        data_proto.add_value(None, response.meta["dict_proto"])
        movie_section_list = response.xpath(
            '//section[@data-accordion-group="movie"]')
        for curr_movie in movie_section_list:
            self.parse_movie(response, curr_movie, data_proto, result_list)

    def parse_movie(self, response, curr_movie, data_proto, result_list):
        """
        parse movie showing data
        """
        title = curr_movie.xpath('./h2/text()').extract_first()
        title_en = curr_movie.xpath('./h2/span/text()').extract_first()
        movie_data_proto = ShowingLoader(response=response)
        movie_data_proto.add_value(None, data_proto.load_item())
        movie_data_proto.add_title(title=title, title_en=title_en)
        title_list = movie_data_proto.get_title_list()
        if not self.is_movie_crawl(title_list):
            return
        show_section_list = curr_movie.xpath('.//ul[@class="timetable"]/li')
        for curr_showing in show_section_list:
            self.parse_showing(response, curr_showing,
                               movie_data_proto, result_list)

    def parse_showing(self, response, curr_showing, data_proto, result_list):
        def parse_time(time_str):
            time = time_str.split(":")
            return (int(time[0]), int(time[1]))

        showing_data_proto = ShowingLoader(response=response)
        showing_data_proto.add_value(None, data_proto.load_item())
        start_time = curr_showing.xpath(
            './span[@class="start-time digit"]/text()').extract_first()
        start_hour, start_minute = parse_time(start_time)
        showing_data_proto.add_value('start_time', self.get_time_from_text(
            start_hour, start_minute))
        end_time = curr_showing.xpath(
            './span[@class="end-time digit"]/text()').extract_first()
        end_hour, end_minute = parse_time(end_time)
        showing_data_proto.add_value('end_time', self.get_time_from_text(
            end_hour, end_minute))
        # TODO cinema name extract failed
        # TODO extract name may be different from real name
        cinema_name = curr_showing.xpath(
            './span[@class="movie-info-theater"]/text()').extract_first()
        # if extract cinema name from showing info, use this one
        if cinema_name:
            showing_data_proto.replace_cinema_name(cinema_name)
        screen_name = "unknown"
        url = curr_showing.xpath(
                './span[@class="purchase-block"]/a/@href').extract_first()
        if url:
            # extract screen name by url parameter
            screen_number = re.findall(r'&sc=(\d+)&', url)
            if screen_number:
                screen_number = screen_number[-1]
                screen_name = "シアター" + screen_number
        # CANNOTSOLVE we cannot get screen name from site for
        # sold out and not sold showings so we have to give it a special
        # screen name
        showing_data_proto.add_screen_name(screen_name)
        showing_data_proto.add_value('seat_type', 'NormalSeat')

        # check whether need to continue crawl booking data or stop now
        if not self.loaded_config['crawl_booking_data']:
            result_list.append(showing_data_proto.load_item())
            return

        booking_data_proto = init_show_booking_loader(response=response)
        booking_data_proto.add_value('showing', showing_data_proto.load_item())
        book_status = curr_showing.xpath(
            './span[@class="purchase-block"]/a/@class').extract_first()
        booking_data_proto.add_book_status(book_status, util=ForumUtil)
        book_status = booking_data_proto.get_output_value('book_status')
        if book_status in ['SoldOut', 'NotSold']:
            # sold out or not sold, set book_seat_count to 0 temporarily
            booking_data_proto.add_value('book_seat_count', 0)
            booking_data_proto.add_time_data()
            result_list.append(booking_data_proto.load_item())
            return
        else:
            # normal, need to crawl book number on order page
            url = curr_showing.xpath(
                './span[@class="purchase-block"]/a/@href').extract_first()
            request = response.follow(url, callback=self.parse)
            self.set_next_func(request, self.parse_normal_showing)
            dict_proto = ShowingBookingLoader.to_dict(
                booking_data_proto.load_item())
            request.meta["dict_proto"] = dict_proto
            result_list.append(request)

    def parse_normal_showing(self, response, result_list):
        self._logger.debug("{} parse_normal_showing".format(self.name))
        result = init_show_booking_loader(
            response=response, item=response.meta["dict_proto"])
        # extract seat info from javascript
        script_text = response.xpath(
            '//script[contains(., "seat_info")]/text()').extract_first()
        m = re.search(r'"total_seats":"(\d+)"', script_text)
        total_seat_count = int(m.group(1))
        m = re.search(r'"unsold_seat_number":"(\d+)"', script_text)
        unsold_seat_count = int(m.group(1))
        booked_seat_count = total_seat_count - unsold_seat_count
        result.add_value('book_seat_count', booked_seat_count)
        result.add_time_data()
        result_list.append(result.load_item())
