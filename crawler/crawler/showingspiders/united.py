# -*- coding: utf-8 -*-
import re
from crawler.showingspiders.showing_spider import ShowingSpider
from crawler.items import (ShowingLoader, ShowingBookingLoader,
                           init_show_booking_loader)
from crawler.utils import UnitedUtil


class UnitedSpider(ShowingSpider):
    """
    united site spider.
    """
    name = "united"
    allowed_domains = ["www.unitedcinemas.jp"]
    """
    start_urls = [
        'http://www.unitedcinemas.jp/index.html'
    ]
    """

    def parse_first_page(self, response, result_list):
        """
        crawl theater list data first
        """
        # TODO cookie issue?
        self._logger.debug("{} parse_first_page".format(self.name))
        theater_list = response.xpath(
            '//section[@class="rcol searchTheater"]//li')
        for theater_element in theater_list:
            if theater_element.xpath('./@class').extract_first() == "area":
                continue
            curr_cinema_url = theater_element.xpath(
                './a/@href').extract_first()
            cinema_img = theater_element.xpath('./img/@src').extract_first()
            cinema_name = theater_element.xpath('./a/img/@alt').extract_first()
            if cinema_img is not None:
                if "icon_uc_ss.gif" in cinema_img:
                    cinema_name = "ユナイテッド・シネマ" + cinema_name
                elif "icon_cpx_ss.gif" in cinema_img:
                    cinema_name = "シネプレックス" + cinema_name
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
            request = response.follow(schedule_url, callback=self.parse)
            self.set_next_func(request, self.parse_cinema)
            request.meta["dict_proto"] = dict(data_proto.load_item())
            result_list.append(request)

    def generate_cinema_schedule_url(self, cinema_name_en, show_day):
        """
        json data url for single cinema, all movies of curr cinema
        """
        date = show_day[:4] + '-' + show_day[4:6] + '-' + show_day[6:]
        url = 'http://www.unitedcinemas.jp/{cinema_name_en}'\
              '/daily.php?date={date}'.format(
                  cinema_name_en=cinema_name_en, date=date)
        return url

    def parse_cinema(self, response, result_list):
        self._logger.debug("{} parse_cinema".format(self.name))
        data_proto = ShowingLoader(response=response)
        data_proto.add_value(None, response.meta["dict_proto"])
        movie_section_list = response.xpath('//ul[@id="dailyList"]/li')
        for curr_movie in movie_section_list:
            self.parse_movie(response, curr_movie, data_proto, result_list)

    def parse_movie(self, response, curr_movie, data_proto, result_list):
        """
        parse movie showing data
        """
        title = curr_movie.xpath('./h3/span/a[1]/text()').extract_first()
        movie_data_proto = ShowingLoader(response=response)
        movie_data_proto.add_value(None, data_proto.load_item())
        movie_data_proto.add_title(title=title)
        title_list = movie_data_proto.get_title_list()
        if not self.is_movie_crawl(title_list):
            return
        screen_section_list = curr_movie.xpath('./ul/li')
        for curr_screen in screen_section_list:
            self.parse_screen(response, curr_screen,
                              movie_data_proto, result_list)

    def parse_screen(self, response, curr_screen, data_proto, result_list):
        screen_data_proto = ShowingLoader(response=response)
        screen_data_proto.add_value(None, data_proto.load_item())
        screen_name = curr_screen.xpath('./p/a/img/@alt').extract_first()
        screen_name = 'screen' + re.findall(r'\d+', screen_name)[0]
        screen_data_proto.add_screen_name(screen_name)
        show_section_list = curr_screen.xpath('./ol/li')
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
            './div/ol/li[@class="startTime"]/text()').extract_first()
        start_hour, start_minute = parse_time(start_time)
        showing_data_proto.add_value('start_time', self.get_time_from_text(
            start_hour, start_minute))
        end_time = curr_showing.xpath(
            './div/ol/li[@class="endTime"]/text()').extract_first()[1:]
        end_hour, end_minute = parse_time(end_time)
        showing_data_proto.add_value('end_time', self.get_time_from_text(
            end_hour, end_minute))
        # handle free order seat type showings
        seat_type = curr_showing.xpath(
            './div/ul/li[@class="seatIcon"]/img/@src').extract_first()
        showing_data_proto.add_value(
            'seat_type', UnitedUtil.standardize_seat_type(seat_type))

        # check whether need to continue crawl booking data or stop now
        if not self.loaded_config['crawl_booking_data']:
            result_list.append(showing_data_proto.load_item())
            return

        booking_data_proto = init_show_booking_loader(response=response)
        booking_data_proto.add_value('showing', showing_data_proto.load_item())
        book_status = curr_showing.xpath(
            './div/ul/li[@class="uolIcon"]//img[1]/@src').extract_first()
        booking_data_proto.add_book_status(book_status, util=UnitedUtil)
        book_status = booking_data_proto.get_output_value('book_status')
        seat_type = showing_data_proto.get_output_value('seat_type')
        if (seat_type == 'FreeSeat' or book_status in ['SoldOut', 'NotSold']):
            # sold out or not sold, set book_seat_count to 0 temporarily
            booking_data_proto.add_value('book_seat_count', 0)
            booking_data_proto.add_time_data()
            result_list.append(booking_data_proto.load_item())
        else:
            # normal, need to crawl book number on order page
            # we will visit schedule page again to generate independent cookie
            # as same cookie will lead to confirm page
            url = curr_showing.xpath(
                './div/ul/li[@class="uolIcon"]/a/@href').extract_first()
            # determine if next page is 4dx confirm page by title
            title = showing_data_proto.get_output_value('title')
            if '4DX' in title:
                request = response.follow(url, callback=self.parse)
                self.set_next_func(request, self.parse_4dx_confirm_page)
            else:
                request = response.follow(url, callback=self.parse)
                self.set_next_func(request, self.parse_normal_showing)
            dict_proto = ShowingBookingLoader.to_dict(
                booking_data_proto.load_item())
            request.meta["dict_proto"] = dict_proto
            # use independent cookie to avoid affecting each other
            request.meta["cookiejar"] = url
            result_list.append(request)

    def parse_4dx_confirm_page(self, response, result_list):
        self._logger.debug("{} parse_4dx_confirm_page".format(self.name))
        url = response.xpath('//form/@action').extract_first()
        request = response.follow(url, method='POST', callback=self.parse)
        self.set_next_func(request, self.parse_normal_showing)
        request.meta["dict_proto"] = response.meta['dict_proto']
        result_list.append(request)

    def parse_normal_showing(self, response, result_list):
        self._logger.debug("{} parse_normal_showing".format(self.name))
        result = init_show_booking_loader(
            response=response, item=response.meta["dict_proto"])
        booked_seat_count = len(response.xpath(
            '//img[contains(@src,"lb_non_selected")]'))
        result.add_value('book_seat_count', booked_seat_count)
        result.add_time_data()
        result_list.append(result.load_item())
