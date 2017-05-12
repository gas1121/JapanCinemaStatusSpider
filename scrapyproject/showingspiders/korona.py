# -*- coding: utf-8 -*-
import re
import json
import scrapy
from scrapyproject.showingspiders.showing_spider import ShowingSpider
from scrapyproject.items import (ShowingLoader, ShowingBookingLoader)
from scrapyproject.utils import KoronaUtil


class KoronaSpider(ShowingSpider):
    """
    korona spider.
    """
    name = "korona"
    start_urls = [
        'http://www.korona.co.jp/cinema/'
    ]

    def parse(self, response):
        """
        crawl theater list data first
        """
        theater_list = response.xpath(
            '//div[@class="LNbowlingList LNshopList"]//a')
        for theater_element in theater_list:
            county_name = theater_element.xpath(
                './text()').extract_first()
            cinema_name = county_name + "コロナシネマワールド"
            data_proto = ShowingLoader(response=response)
            data_proto.add_cinema_name(cinema_name)
            cinema_name = data_proto.get_output_value('cinema_name')
            if not self.is_cinema_crawl([cinema_name]):
                continue
            curr_cinema_url = theater_element.xpath(
                './@href').extract_first()
            data_proto.add_cinema_site(curr_cinema_url, cinema_name)
            data_proto.add_value('source', self.name)
            cinema_name_en = curr_cinema_url.split('/')[-2]
            schedule_url = self.generate_cinema_schedule_url(
                cinema_name_en, self.date)
            request = scrapy.Request(
                schedule_url, callback=self.parse_cinema)
            request.meta["data_proto"] = data_proto
            yield request

    def generate_cinema_schedule_url(self, cinema_name, date):
        """
        schedule url for single cinema, all movies of curr cinema
        """
        used_date = date[2:]
        url = 'http://www.korona.co.jp/Cinema/{cinema_name}/'\
              'List_Renew/{date}.asp'.format(
                  cinema_name=cinema_name, date=used_date)
        return url

    def parse_cinema(self, response):
        data_proto = ShowingLoader(response=response)
        data_proto.add_value(None, response.meta["data_proto"].load_item())
        result_list = []
        movie_list = response.xpath('//div[@class="wrapFilm"]')
        for curr_movie in movie_list:
            self.parse_movie(response, curr_movie, data_proto, result_list)
        for result in result_list:
            if result:
                yield result

    def parse_movie(self, response, curr_movie, data_proto, result_list):
        """
        parse movie showing data
        """
        title = curr_movie.xpath('./h4/a/text()').extract_first()
        if not title:
            title = curr_movie.xpath('./h4/text()').extract_first()
        movie_data_proto = ShowingLoader(response=response)
        movie_data_proto.add_value(None, data_proto.load_item())
        movie_data_proto.add_title(title=title)
        title_list = movie_data_proto.get_title_list()
        if not self.is_movie_crawl(title_list):
            return
        showing_list = curr_movie.xpath('.//table//tr')
        for curr_showing in showing_list:
            self.parse_showing(response, curr_showing,
                               movie_data_proto, result_list)

    def parse_showing(self, response, curr_showing, data_proto, result_list):
        def parse_time(time_str):
            time = time_str.split(":")
            return (int(time[0]), int(time[1]))
        showing_data_proto = ShowingLoader(response=response)
        showing_data_proto.add_value(None, data_proto.load_item())
        screen_name = curr_showing.xpath('./th/div/text()').extract_first()
        showing_data_proto.add_screen_name(screen_name)
        start_time = curr_showing.xpath(
            './td[@class="time"]/div/text()').extract_first()
        start_hour, start_minute = parse_time(start_time)
        showing_data_proto.add_value('start_time', self.get_time_from_text(
            start_hour, start_minute))
        end_time = curr_showing.xpath(
            './td[@class="time"]/div/span/text()').extract_first()[1:]
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
        booking_data_proto.context['util'] = KoronaUtil
        booking_data_proto.context['loader'] = booking_data_proto
        booking_data_proto.add_value('showing', showing_data_proto.load_item())
        book_status = curr_showing.xpath(
            './/img[contains(@src,"icon_seat_vacant")]/@alt').extract_first()
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
            url = curr_showing.xpath(
                './td[@class="btnReservation"]/div/a/@href').extract_first()
            request = scrapy.Request(url, callback=self.parse_normal_showing)
            request.meta["data_proto"] = booking_data_proto
            result_list.append(request)

    def parse_normal_showing(self, response):
        seat_block = response.xpath('//div[@class="cinema_seets step1"]')
        all_li = len(seat_block.xpath('.//li'))
        useless_li = (
            len(seat_block.xpath('.//li[contains(@class,"none")]'))
            + len(seat_block.xpath(
                './/li[contains(@class,"seet_row_head")]')))
        total_seat_count = all_li - useless_li
        result = response.meta["data_proto"]
        result.get_output_value(
            'showing')['total_seat_count'] = total_seat_count
        # empty seat is generated by json api, so we need another request
        # extract json url from javascript
        script_text = response.xpath(
            '//script[contains(.,"ajax")]/text()').extract_first()
        m = re.search(r"url: \"(.+)\"", script_text)
        tail = m.group(1)
        m = re.search(r"data: \"(.+)\"", script_text)
        parameters = m.group(1)
        url = self.generate_seat_json_url(tail=tail, parameters=parameters)
        request = scrapy.Request(url, callback=self.parse_showing_seat_json)
        request.meta["data_proto"] = result
        yield request

    def generate_seat_json_url(self, tail, parameters):
        url = "https://www.korona.co.jp/Cinema/nresrv/{tail}?"\
              "{parameters}".format(tail=tail, parameters=parameters)
        return url

    def parse_showing_seat_json(self, response):
        try:
            seat_data = json.loads(response.text)
        except json.JSONDecodeError:
            return
        result = response.meta["data_proto"]
        empty_seat_count = len(seat_data)
        booked_seat_count = (
            result.get_output_value('showing')['total_seat_count']
            - empty_seat_count)
        result.add_value('book_seat_count', booked_seat_count)
        result.add_time_data()
        yield result.load_item()
