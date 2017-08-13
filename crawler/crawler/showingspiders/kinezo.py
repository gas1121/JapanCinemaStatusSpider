# -*- coding: utf-8 -*-
from crawler.showingspiders.showing_spider import ShowingSpider
from crawler.items import (ShowingLoader, ShowingBookingLoader,
                           init_show_booking_loader)
from crawler.utils import KinezoUtil


class KinezoSpider(ShowingSpider):
    """
    kinezo site spider.
    """
    name = "kinezo"
    allowed_domains = ['kinezo.jp']
    """
    start_urls = [
        'http://kinezo.jp/pc/'
    ]
    """
    
    def parse_first_page(self, response, result_list):
        """
        crawl theater list data first
        """
        self._logger.debug("{} parse_first_page".format(self.name))
        theater_list = response.xpath(
            '//footer/p[position()>=2 and position() <=3]//a')
        # partner cinema is not included
        for theater_element in theater_list:
            curr_cinema_url = theater_element.xpath(
                './@href').extract_first()
            cinema_name = theater_element.xpath('./text()').extract_first()
            data_proto = ShowingLoader(response=response)
            data_proto.add_cinema_name(cinema_name)
            cinema_name = data_proto.get_output_value('cinema_name')
            data_proto.add_cinema_site(curr_cinema_url, cinema_name)
            data_proto.add_value('source', self.name)
            if not self.is_cinema_crawl([cinema_name]):
                continue
            cinema_name_en = curr_cinema_url.split('/')[-1].split('?')[0]
            request = response.follow(curr_cinema_url, callback=self.parse)
            self.set_next_func(request, self.parse_main_page)
            request.meta["dict_proto"] = dict(data_proto.load_item())
            request.meta["cinema_name_en"] = cinema_name_en
            request.meta["dont_merge_cookies"] = True
            result_list.append(request)

    def parse_main_page(self, response, result_list):
        """
        cinema main page

        generate cookie here
        """
        self._logger.debug("{} parse_main_page".format(self.name))
        cinema_name_en = response.meta["cinema_name_en"]
        schedule_url = self.generate_cinema_schedule_url(
            cinema_name_en, self.loaded_config['date'])
        request = response.follow(schedule_url, callback=self.parse)
        self.set_next_func(request, self.parse_cinema)
        request.meta["dict_proto"] = response.meta["dict_proto"]
        result_list.append(request)

    def generate_cinema_schedule_url(self, cinema_name_en, show_day):
        """
        schedule url for single cinema, all movies of curr cinema
        """
        url = 'http://kinezo.jp/pc/{name}/schedule/index/{y}/{m}/{d}'.format(
                  name=cinema_name_en, y=show_day[:4], m=show_day[4:6],
                  d=show_day[6:])
        return url

    def parse_cinema(self, response, result_list):
        """
        cinema home page
        we have to pass this page to get independent cookie for each cinema
        """
        self._logger.debug("{} parse_cinema".format(self.name))
        print(response.headers.getlist('Set-Cookie'))        
        data_proto = ShowingLoader(response=response)
        data_proto.add_value(None, response.meta["dict_proto"])
        movie_title_list = response.xpath('//div[@class="cinemaTitle elp"]')
        movie_section_list = response.xpath('//div[@class="theaterListWrap"]')
        for curr_movie in zip(movie_title_list, movie_section_list):
            self.parse_movie(response, curr_movie, data_proto, result_list)

    def parse_movie(self, response, curr_movie, data_proto, result_list):
        """
        parse movie showing data

        curr_movie is a tuple
        """
        title_section, detail_section = curr_movie
        title = ''.join(title_section.xpath('./text()').extract())
        movie_data_proto = ShowingLoader(response=response)
        movie_data_proto.add_value(None, data_proto.load_item())
        movie_data_proto.add_title(title=title)
        title_list = movie_data_proto.get_title_list()
        if not self.is_movie_crawl(title_list):
            return
        screen_section_list = detail_section.xpath('.//table')
        for curr_screen in screen_section_list:
            self.parse_screen(response, curr_screen,
                              movie_data_proto, result_list)

    def parse_screen(self, response, curr_screen, data_proto, result_list):
        screen_data_proto = ShowingLoader(response=response)
        screen_data_proto.add_value(None, data_proto.load_item())
        screen_name = curr_screen.xpath('./tr/td[1]/text()').extract_first()
        screen_data_proto.add_screen_name(screen_name)
        show_section_list = curr_screen.xpath('./tr/td[2]/a')
        for curr_showing in show_section_list:
            self.parse_showing(response, curr_showing,
                               screen_data_proto, result_list)

    def parse_showing(self, response, curr_showing, data_proto, result_list):
        showing_data_proto = ShowingLoader(response=response)
        showing_data_proto.add_value(None, data_proto.load_item())
        start_time = curr_showing.xpath(
            './div/text()').extract_first()[:-1]
        start_hour, start_minute = self.parse_time(start_time)
        showing_data_proto.add_value('start_time', self.get_time_from_text(
            start_hour, start_minute))
        # end time not displayed in schedule page

        showing_data_proto.add_value('seat_type', 'NormalSeat')

        # check whether need to continue crawl booking data or stop now
        if not self.loaded_config['crawl_booking_data']:
            result_list.append(showing_data_proto.load_item())
            return

        booking_data_proto = init_show_booking_loader(response=response)
        booking_data_proto.add_value('showing', showing_data_proto.load_item())
        book_status = curr_showing.xpath('./div/@class').extract_first()
        booking_data_proto.add_book_status(book_status, util=KinezoUtil)
        book_status = booking_data_proto.get_output_value('book_status')
        if book_status in ['SoldOut', 'NotSold']:
            # sold out or not sold, set book_seat_count to 0 temporarily
            booking_data_proto.add_value('book_seat_count', 0)
            booking_data_proto.add_time_data()
            result_list.append(booking_data_proto.load_item())
        else:
            # normal, need to crawl book number on order page
            url = curr_showing.xpath('./@href').extract_first()
            request = response.follow(url, callback=self.parse)
            self.set_next_func(request, self.parse_normal_showing)
            dict_proto = ShowingBookingLoader.to_dict(
                booking_data_proto.load_item())
            request.meta["dict_proto"] = dict_proto
            result_list.append(request)

    def parse_normal_showing(self, response, result_list):
        self._logger.debug("{} parse_normal_showing".format(self.name))
        print(response.headers.getlist('Set-Cookie'))
        print("ブラウザのセッション" in response.text)
        result = init_show_booking_loader(
            response=response, item=response.meta["dict_proto"])
        time_text = response.xpath(
            '//span[@class="screenTime"]/text()').extract_first()
        time_list = time_text.split('-')
        start_time = time_list[0].strip()
        start_hour, start_minute = self.parse_time(start_time)
        result.get_output_value('showing')['start_time'] = \
            self.get_time_from_text(start_hour, start_minute)
        end_time = time_list[1].strip()
        end_hour, end_minute = self.parse_time(end_time)
        result.get_output_value('showing')['end_time'] = \
            self.get_time_from_text(end_hour, end_minute)

        booked_seat_count = len(response.xpath(
            '//li[@class="seatSell seatOff"]'))
        result.add_value('book_seat_count', booked_seat_count)
        result.add_time_data()
        result_list.append(result.load_item())

    def parse_time(self, time_str):
        time = time_str.split(":")
        return (int(time[0]), int(time[1]))
