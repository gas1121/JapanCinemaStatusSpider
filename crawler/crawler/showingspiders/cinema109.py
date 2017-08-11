# -*- coding: utf-8 -*-
import re
from crawler.showingspiders.showing_spider import ShowingSpider
from crawler.items import (ShowingLoader, ShowingBookingLoader,
                           init_show_booking_loader)
from crawler.utils import Cinema109Util


class Cinema109Spider(ShowingSpider):
    """
    109 site spider.
    """
    name = "cinema109"
    allowed_domains = ['109cinemas.net', 'cinema.109cinemas.net']
    """
    start_urls = [
        'http://109cinemas.net/'
    ]
    """

    def parse_first_page(self, response, result_list):
        """
        crawl theater list data first
        """
        # TODO not tested
        self._logger.debug("{} parse_first_page".format(self.name))
        theater_list = response.xpath('//section[@id="theatres"]//a')
        for theater_element in theater_list:
            curr_cinema_url = theater_element.xpath(
                './@href').extract_first()
            cinema_name = theater_element.xpath('./text()').extract_first()
            if cinema_name != "ムービル":
                cinema_name = "109シネマズ" + cinema_name
            data_proto = ShowingLoader(response=response)
            data_proto.add_cinema_name(cinema_name)
            cinema_name = data_proto.get_output_value('cinema_name')
            data_proto.add_cinema_site(
                response.urljoin(curr_cinema_url), cinema_name)
            data_proto.add_value('source', self.name)
            if not self.is_cinema_crawl([cinema_name]):
                continue
            cinema_name_en = curr_cinema_url.split('/')[-2]
            schedule_url = self.generate_cinema_schedule_url(
                cinema_name_en, self.loaded_config['date'])
            request = response.follow(schedule_url, callback=self.parse_cinema)
            self.set_next_func(request, self.parse_cinema)
            request.meta["dict_proto"] = dict(data_proto.load_item())
            result_list.append(request)

    def generate_cinema_schedule_url(self, cinema_name_en, show_day):
        """
        schedule url for single cinema, all movies of curr cinema
        """
        url = 'http://109cinemas.net/{cinema_name_en}/schedules/{date}.html'\
              '/daily.php?date={date}'.format(
                  cinema_name_en=cinema_name_en, date=show_day)
        return url

    def parse_cinema(self, response, result_list):
        self._logger.debug("{} parse_cinema".format(self.name))
        data_proto = ShowingLoader(response=response)
        data_proto.add_value(None, response.meta["dict_proto"])
        movie_section_list = response.xpath('//div[@id="timetable"]/article')
        for curr_movie in movie_section_list:
            self.parse_movie(response, curr_movie, data_proto, result_list)

    def parse_movie(self, response, curr_movie, data_proto, result_list):
        """
        parse movie showing data
        """
        title = curr_movie.xpath('./header//h2/text()').extract_first()
        title_en = curr_movie.xpath('./header//p/text()').extract_first()
        movie_data_proto = ShowingLoader(response=response)
        movie_data_proto.add_value(None, data_proto.load_item())
        movie_data_proto.add_title(title=title, title_en=title_en)
        title_list = movie_data_proto.get_title_list()
        if not self.is_movie_crawl(title_list):
            return
        screen_section_list = curr_movie.xpath('./ul')
        for curr_screen in screen_section_list:
            self.parse_screen(response, curr_screen,
                              movie_data_proto, result_list)

    def parse_screen(self, response, curr_screen, data_proto, result_list):
        screen_data_proto = ShowingLoader(response=response)
        screen_data_proto.add_value(None, data_proto.load_item())
        screen_name = ''.join(curr_screen.xpath(
            './li[@class="theatre"]/a//text()').extract())
        screen_data_proto.add_screen_name(screen_name)
        show_section_list = curr_screen.xpath('./li')[1:]
        for curr_showing in show_section_list:
            self.parse_showing(response, curr_showing,
                               screen_data_proto, result_list)

    def parse_showing(self, response, curr_showing, data_proto, result_list):
        def parse_time(time_str):
            time = time_str.split(":")
            return (int(time[0]), int(time[1]))

        showing_data_proto = ShowingLoader(response=response)
        showing_data_proto.add_value(None, data_proto.load_item())
        start_time = curr_showing.xpath(
            './/time[@class="start"]/text()').extract_first()
        start_hour, start_minute = parse_time(start_time)
        showing_data_proto.add_value('start_time', self.get_time_from_text(
            start_hour, start_minute))
        end_time = curr_showing.xpath(
            './/time[@class="end"]/text()').extract_first()
        end_hour, end_minute = parse_time(end_time)
        showing_data_proto.add_value('end_time', self.get_time_from_text(
            end_hour, end_minute))
        showing_data_proto.add_value('seat_type', 'NormalSeat')

        # check whether need to continue crawl booking data or stop now
        if not self.loaded_config['crawl_booking_data']:
            result_list.append(showing_data_proto.load_item())
            return

        booking_data_proto = init_show_booking_loader(response=response)
        booking_data_proto.add_value('showing', showing_data_proto.load_item())
        book_status = curr_showing.xpath(
            './a/div/@class').extract_first()
        booking_data_proto.add_book_status(book_status, util=Cinema109Util)
        book_status = booking_data_proto.get_output_value('book_status')
        if book_status in ['SoldOut', 'NotSold']:
            # sold out or not sold, set book_seat_count to 0 temporarily
            booking_data_proto.add_value('book_seat_count', 0)
            booking_data_proto.add_time_data()
            result_list.append(booking_data_proto.load_item())
            return
        else:
            # normal, need to crawl book number on order page
            url = curr_showing.xpath('./a/@href').extract_first()
            request = response.follow(url, callback=self.parse)
            self.set_next_func(request, self.parse_normal_showing)
            dict_proto = ShowingBookingLoader.to_dict(
                booking_data_proto.load_item())
            request.meta["dict_proto"] = dict_proto
            result_list.append(request)

    def parse_normal_showing(self, response, result_list):
        """
        parse seat order page
        """
        self._logger.debug("{} parse_normal_showing".format(self.name))
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
        request = response.follow(url, method='POST', callback=self.parse)
        self.set_next_func(request, self.parse_seat_json_api)
        request.meta["dict_proto"] = response.meta['dict_proto']
        result_list.append(request)

    def parse_seat_json_api(self, response, result_list):
        self._logger.debug("{} parse_seat_json_api".format(self.name))
        result = init_show_booking_loader(
            response=response, item=response.meta["dict_proto"])
        booked_normal_seat_count = len(response.xpath(
            '//a[@class="seat seat-none"]'))
        booked_wheelseat_count = len(response.xpath(
            '//a[@class="seat wheelseat-none"]'))
        booked_executive_seat_count = len(response.xpath(
            '//a[@class="seat executive-none"]'))
        booked_seat_count = (
            booked_normal_seat_count + booked_wheelseat_count +
            booked_executive_seat_count)
        result.add_value('book_seat_count', booked_seat_count)
        result.add_time_data()
        result_list.append(result.load_item())
