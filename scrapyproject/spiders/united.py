# -*- coding: utf-8 -*-
import unicodedata
import json
import copy
import arrow
import scrapy
from scrapyproject.spiders.showing_spider import ShowingSpider
from scrapyproject.items import (Showing, standardize_cinema_name,
                                 standardize_screen_name)
from scrapyproject.utils.site_utils import UnitedUtil


class UnitedSpider(ShowingSpider):
    """
    united site spider.
    """
    name = "united"
    allowed_domains = ["www.unitedcinemas.jp"]
    start_urls = [
        'http://www.unitedcinemas.jp/index.html'
    ]

    cinema_list = ['ユナイテッド・シネマとしまえん']

    def parse(self, response):
        """
        crawl theater list data first
        """
        # TODO proxy encode problem
        theater_list = response.xpath(
            '//section[@class="rcol searchTheater"]//a')
        for theater_element in theater_list:
            curr_cinema_url = theater_element.xpath(
                './@href').extract_first()
            cinema_name_en = curr_cinema_url.split('/')[-2]
            # TEST
            if cinema_name_en != "toshimaen":
                continue
            schedule_url = self.generate_cinema_schedule_url(
                cinema_name_en, self.date)
            request = scrapy.Request(schedule_url, callback=self.parse_cinema)
            request.meta["cinema_site"] = response.urljoin(curr_cinema_url)
            # keep schedule url for later use
            request.meta["schedule_url"] = schedule_url
            yield request

    def generate_cinema_schedule_url(self, cinema_name_en, show_day):
        """
        json data url for single cinema, all movies of curr cinema
        """
        date = show_day[:4] + '-' + show_day[4:6] + '-' + show_day[6:]
        url = 'http://www.unitedcinemas.jp/{cinema_name_en}'\
              '/daily.php?date={date}'.format(
                  cinema_name_en=cinema_name_en, date=date)
        return url

    def parse_cinema(self, response):
        print('parse_cinema')
        cinema_name = response.xpath('//header/h1/a/img/@alt').extract_first()
        standardize_cinema_name(cinema_name)
        if not self.is_cinema_crawl([cinema_name]):
            return
        data_proto = Showing()
        data_proto['cinema_name'] = cinema_name
        data_proto["cinema_site"] = response.meta['cinema_site']
        result_list = []
        movie_section_list = response.xpath('//ul[@id="dailyList"]/li')
        for curr_movie in movie_section_list:
            self.parse_movie(response, curr_movie, data_proto, result_list)
        for result in result_list:
            if result:
                yield result

    def parse_movie(self, response, curr_movie, data_proto, result_list):
        """
        parse movie showing data
        """
        print('parse_movie')
        title = curr_movie.xpath('./h3/span/a[1]/text()').extract_first()
        title_list = [title]
        if not self.is_movie_crawl(title_list):
            return
        movie_data_proto = copy.deepcopy(data_proto)
        movie_data_proto['title'] = title
        screen_section_list = curr_movie.xpath('./ul/li')
        for curr_screen in screen_section_list:
            self.parse_screen(response, curr_screen,
                              movie_data_proto, result_list)

    def parse_screen(self, response, curr_screen, data_proto, result_list):
        print('parse_screen')        
        screen_data_proto = copy.deepcopy(data_proto)
        screen_name = curr_screen.xpath('./p/a/img/@alt').extract_first()
        screen_data_proto['screen'] = standardize_screen_name(
            screen_name, screen_data_proto['cinema_name'])
        show_section_list = curr_screen.xpath('./ol/li')
        for curr_showing in show_section_list:
            self.parse_showing(response, curr_showing,
                               screen_data_proto, result_list)

    def parse_showing(self, response, curr_showing, data_proto, result_list):
        def parse_time(time_str):
            time = time_str.split(":")
            return (int(time[0]), int(time[1]))
        print('parse_showing')

        showing_data_proto = copy.deepcopy(data_proto)
        start_time = curr_showing.xpath(
            './div/ol/li[@class="startTime"]/text()').extract_first()
        start_hour, start_minute = parse_time(start_time)
        showing_data_proto['start_time'] = self.get_time_from_text(
            start_hour, start_minute)
        end_time = curr_showing.xpath(
            './div/ol/li[@class="endTime"]/text()').extract_first()[1:]
        end_hour, end_minute = parse_time(end_time)
        showing_data_proto['end_time'] = self.get_time_from_text(
            end_hour, end_minute)
        book_status = curr_showing.xpath(
            './div/ul/li[@class="uolIcon"]//img[1]/@src').extract_first()
        showing_data_proto['book_status'] = \
            UnitedUtil.standardize_book_status(book_status)
        if showing_data_proto['book_status'] in ['SoldOut', 'NotSold']:
            # sold out or not sold, seat set to 0
            showing_data_proto['book_seat_count'] = 0
            showing_data_proto['total_seat_count'] = 0
            showing_data_proto['record_time'] = arrow.now()
            showing_data_proto['source'] = self.name
            result_list.append(showing_data_proto)
            return
        else:
            # normal, need to crawl book number on order page
            # we will visit schedule page again to generate independent cookie
            # as same cookie will lead to confirm page
            url = curr_showing.xpath(
                './div/ul/li[@class="uolIcon"]/a/@href').extract_first()
            schedule_url = response.meta['schedule_url']
            request = scrapy.Request(
                schedule_url, dont_filter=True, callback=self.refresh_cookie)
            request.meta["data_proto"] = showing_data_proto
            request.meta["url"] = url
            request.meta["dont_merge_cookies"] = True
            result_list.append(request)

    def refresh_cookie(self, response):
        """
        generate new cookie for each showing to avoid conflict
        """
        # TODO remove this function and put request in list to avoid cookie 
        # conflict 
        print('refresh_cookie')
        print(response.headers.getlist('Set-Cookie'))
        url = response.meta["url"]
        # determine if next page is 4dx confirm page by title
        if '4DX' in response.meta['data_proto']['title']:
            request = scrapy.Request(url, callback=self.parse_4dx_confirm_page)
        else:
            request = scrapy.Request(url, callback=self.parse_normal_showing)
        request.meta["data_proto"] = response.meta['data_proto']
        yield request

    def parse_4dx_confirm_page(self, response):
        # TODO pass confirm page
        print('parse_4dx_confirm_page')
        pass

    def parse_normal_showing(self, response):
        print('parse_normal_showing')
        print(response.meta['data_proto']['title'])
        result = response.meta["data_proto"]
        total_seat_count = int(response.xpath(
            '//span[@class="seat"]/text()').extract_first())
        result['book_seat_count'] = len(response.xpath(
            '//img[contains(@src,"lb_non_selected")]'))
        result['total_seat_count'] = total_seat_count
        result['record_time'] = arrow.now()
        result['source'] = self.name
        yield result
