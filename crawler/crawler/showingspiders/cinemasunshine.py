# -*- coding: utf-8 -*-
import re
import json
import scrapy
from crawler.showingspiders.showing_spider import ShowingSpider
from crawler.items import (ShowingLoader, init_show_booking_loader)
from crawler.utils import CinemaSunshineUtil


class CinemaSunshineSpider(ShowingSpider):
    """
    Cinema Sunshine spider.
    """
    name = "cinemasunshine"
    start_urls = [
        'http://www.cinemasunshine.co.jp/theater/'
    ]

    def parse(self, response):
        """
        crawl theater list data first
        """
        theater_list = response.xpath('//li[@class="clearfix"]')
        for theater_element in theater_list:
            cinema_name = theater_element.xpath(
                './p[@class="theaterName"]/a/text()').extract_first()
            data_proto = ShowingLoader(response=response)
            data_proto.add_cinema_name(cinema_name)
            cinema_name = data_proto.get_output_value('cinema_name')
            if not self.is_cinema_crawl([cinema_name]):
                continue
            curr_cinema_url = theater_element.xpath(
                './p[@class="theaterName"]/a/@href').extract_first()
            data_proto.add_cinema_site(
                response.urljoin(curr_cinema_url), cinema_name)
            data_proto.add_value('source', self.name)
            cinema_name_en = curr_cinema_url.split('/')[-1]
            json_url = self.generate_cinema_schedule_url(
                cinema_name_en, self.date)
            request = response.follow(json_url, callback=self.parse_cinema)
            request.meta["data_proto"] = data_proto.load_item()
            yield request

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
        data_proto = ShowingLoader(response=response)
        data_proto.add_value(None, response.meta["data_proto"])
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
        movie_data_proto = ShowingLoader(response=response)
        movie_data_proto.add_value(None, data_proto.load_item())
        movie_data_proto.add_title(title=title)
        title_list = movie_data_proto.get_title_list()
        if not self.is_movie_crawl(title_list):
            return
        screen_list = []
        if isinstance(curr_movie['screen'], dict):
            screen_list.append(curr_movie['screen'])
        else:
            screen_list = curr_movie['screen']
        for curr_screen in screen_list:
            self.parse_screen(response, curr_screen,
                              movie_data_proto, result_list)

    def parse_screen(self, response, curr_screen, data_proto, result_list):
        screen = curr_screen['name']
        screen_data_proto = ShowingLoader(response=response)
        screen_data_proto.add_value(None, data_proto.load_item())
        screen_data_proto.add_screen_name(screen)
        showing_list = []
        if isinstance(curr_screen['time'], dict):
            showing_list.append(curr_screen['time'])
        else:
            showing_list = curr_screen['time']
        for curr_showing in showing_list:
            self.parse_showing(response, curr_showing,
                               screen_data_proto, result_list)

    def parse_showing(self, response, curr_showing, data_proto, result_list):
        def parse_time(time_str):
            return (int(time_str[:2]), int(time_str[2:]))
        showing_data_proto = ShowingLoader(response=response)
        showing_data_proto.add_value(None, data_proto.load_item())
        start_hour, start_minute = parse_time(curr_showing['start_time'])
        showing_data_proto.add_value('start_time', self.get_time_from_text(
            start_hour, start_minute))
        end_hour, end_minute = parse_time(curr_showing['end_time'])
        showing_data_proto.add_value('end_time', self.get_time_from_text(
            end_hour, end_minute))
        showing_data_proto.add_value('seat_type', 'NormalSeat')
        # TODO get seat type right now

        # query screen number from database
        showing_data_proto.add_total_seat_count()
        # check whether need to continue crawl booking data or stop now
        if not self.crawl_booking_data:
            result_list.append(showing_data_proto.load_item())
            return

        booking_data_proto = init_show_booking_loader(response=response)
        booking_data_proto.add_value('showing', showing_data_proto.load_item())
        booking_data_proto.add_book_status(
            curr_showing['available'], util=CinemaSunshineUtil)
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
            # with new cinema opened, there are now two online booking system
            # exist.
            url = curr_showing['url']
            if 'ticket-cinemasunshine.com' in url:
                # new online booking system
                request = response.follow(
                    url, callback=self.parse_new_pre_ordering)
            else:
                request = response.follow(
                    url, callback=self.parse_pre_ordering)
            request.meta["dont_merge_cookies"] = True
            request.meta["data_proto"] = booking_data_proto.load_item()
            result_list.append(request)

    def parse_pre_ordering(self, response):
        """
        redirect with form data
        """
        # TODO form not found bug
        request = scrapy.FormRequest.from_response(
            response, formxpath='//form', callback=self.parse_agreement)
        request.meta["data_proto"] = response.meta["data_proto"]
        request.meta["dont_merge_cookies"] = True
        yield request

    def parse_agreement(self, response):
        """
        agreement page
        """
        check_value = response.xpath(
            '//input[@type="checkbox"]/@value').extract_first()
        request = scrapy.FormRequest.from_response(
            response, formxpath='//form[@name="FORM1"]',
            formdata={'agre': 'agr', 'p_agree[]': check_value},
            callback=self.parse_select_ticket_count)
        request.meta["data_proto"] = response.meta["data_proto"]
        request.meta["dont_merge_cookies"] = True
        yield request

    def parse_select_ticket_count(self, response):
        """
        ticket number select page
        """
        request = scrapy.FormRequest.from_response(
            response, formxpath='//form[@name="FORM1"]',
            formdata={'goArea': 'goArea', 'ninzu[]': "1"},
            callback=self.parse_normal_showing)
        request.meta["data_proto"] = response.meta["data_proto"]
        request.meta["dont_merge_cookies"] = True
        yield request

    def parse_normal_showing(self, response):
        # some cinemas are free seat ordered, so data may not be crawled
        booked_seat_count = len(response.xpath(
            '//img[contains(@src,"seat_102.gif")]'))
        result = init_show_booking_loader(
            response=response, item=response.meta["data_proto"])
        result.add_value('book_seat_count', booked_seat_count)
        result.add_time_data()
        yield result.load_item()

    def parse_new_pre_ordering(self, response):
        showing_number = re.sub(r"^.*id=([0-9]+)$", r"\1", response.url)
        url = "https://ticket-cinemasunshine.com/purchase/transaction"
        form_data = {"id": showing_number}
        request = scrapy.FormRequest(
            url, formdata=form_data, callback=self.parse_new_redirect)
        request.meta["data_proto"] = response.meta["data_proto"]
        yield request

    def parse_new_redirect(self, response):
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            return
        request = response.follow(data["redirect"],
                                  callback=self.parse_new_normal_showing)
        request.meta["data_proto"] = response.meta["data_proto"]
        yield request

    def parse_new_normal_showing(self, response):
        """
        new booking system
        """
        screen_div = response.xpath('//div[contains(@class,"screen-cover")]')
        theater_code = screen_div.xpath('./@data-theater').extract_first()
        date_jouei = screen_div.xpath('./@data-day').extract_first()
        title_code = screen_div.xpath('./@data-coa-title-code').extract_first()
        title_branch_num = screen_div.xpath(
            './@data-coa-title-branch-num').extract_first()
        time_begin = screen_div.xpath('./@data-time-start').extract_first()
        screen_code = screen_div.xpath('./@data-screen-code').extract_first()
        form_data = {
            "theater_code": theater_code,
            "date_jouei": date_jouei,
            "title_code": title_code,
            "title_branch_num": title_branch_num,
            "time_begin": time_begin,
            "screen_code": screen_code,
        }
        url = 'https://ticket-cinemasunshine.com/purchase/'\
              'getScreenStateReserve'
        request = scrapy.FormRequest(
            url, formdata=form_data,
            callback=self.parse_new_normal_showing_json)
        request.meta["data_proto"] = response.meta["data_proto"]
        yield request

    def parse_new_normal_showing_json(self, response):
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            return
        result = init_show_booking_loader(
            response=response, item=response.meta["data_proto"])
        seat_map = data["result"]["screen"]["map"]
        total_seat_count = sum((x.count(1) + x.count(4) + x.count(5))
                               for x in seat_map)
        empty_seats = data["result"]["state"]["list_seat"][0]["list_free_seat"]
        empty_seat_count = len(empty_seats)
        booked_seat_count = total_seat_count - empty_seat_count
        result.add_value('book_seat_count', booked_seat_count)
        result.add_time_data()
        yield result.load_item()
