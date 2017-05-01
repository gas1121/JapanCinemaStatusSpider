# -*- coding: utf-8 -*-
import scrapy
from scrapyproject.showingspiders.showing_spider import ShowingSpider
from scrapyproject.items import (ShowingLoader, ShowingBookingLoader)
from scrapyproject.utils import KinezoUtil


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
            data_proto = ShowingLoader(response=response)
            data_proto.add_cinema_name(cinema_name)
            cinema_name = data_proto.get_output_value('cinema_name')
            data_proto.add_cinema_site(curr_cinema_url, cinema_name)
            data_proto.add_value('source', self.name)
            if not self.is_cinema_crawl([cinema_name]):
                continue
            cinema_name_en = curr_cinema_url.split('/')[-1].split('?')[0]
            request = scrapy.Request(
                curr_cinema_url, callback=self.parse_main_page)
            request.meta["data_proto"] = data_proto
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
        request.meta["data_proto"] = response.meta["data_proto"]
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
        data_proto = ShowingLoader(response=response)
        data_proto.add_value(None, response.meta["data_proto"].load_item())
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

        # query screen number from database
        showing_data_proto.add_total_seat_count()
        # check whether need to continue crawl booking data or stop now
        if not self.crawl_booking_data:
            result_list.append(showing_data_proto)
            return

        booking_data_proto = ShowingBookingLoader(response=response)
        booking_data_proto.context['util'] = KinezoUtil
        booking_data_proto.context['loader'] = booking_data_proto
        booking_data_proto.add_value('showing', showing_data_proto.load_item())
        book_status = curr_showing.xpath('./div/@class').extract_first()
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
        yield result.load_item()

    def parse_time(self, time_str):
        time = time_str.split(":")
        return (int(time[0]), int(time[1]))
