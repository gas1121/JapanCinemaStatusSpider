# -*- coding: utf-8 -*-
import re
import copy
import arrow
import scrapy
from scrapyproject.spiders.showing_spider import ShowingSpider
from scrapyproject.items import (Showing, standardize_cinema_name,
                                 standardize_screen_name)
from scrapyproject.utils.site_utils import UnitedUtil


class MovieSpider(ShowingSpider):
    """
    movix site spider.
    """
    name = "movix"
    allowed_domains = [
        'www.smt-cinema.com',
        'www.parkscinema.com',
        'www.osakastationcitycinema.com'
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
            cinema_name = standardize_cinema_name(cinema_name)
            if not self.is_cinema_crawl([cinema_name]):
                continue
            request = scrapy.Request(
                curr_cinema_url, callback=self.parse_cinema)
            request.meta["cinema_name"] = cinema_name
            request.meta["cinema_site"] = curr_cinema_url
            yield request

    def parse_cinema(self, response):
        """
        get cinema code from homepage's javascript
        """
        script_text = response.xpath(
            '//script[contains(.,"thnumber")]/text()').extract_first()
        thnumber = re.findall(r'\d+', script_text)[0]
        schedule_url = self.generate_cinema_schedule_url(
            thnumber, self.date)
        request = scrapy.Request(
            schedule_url, encoding='utf-8', callback=self.parse_shechedule)
        request.meta["cinema_name"] = response.meta["cinema_name"]
        request.meta["cinema_site"] = response.meta["cinema_site"]
        yield request

    def generate_cinema_schedule_url(self, thnumber, show_day):
        """
        schedule url for single cinema, all movies of curr cinema
        """
        url = 'http://www.smt-cinema.com/schedule/pc/s0100_'\
              '{thnumber}_{show_day}.html'.format(
                  thnumber=thnumber, show_day=show_day)
        return url

    def parse_shechedule(self, response):
        data_proto = Showing()
        data_proto['cinema_name'] = response.meta['cinema_name']
        data_proto["cinema_site"] = response.meta['cinema_site']
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
        title_list = [title]
        if not self.is_movie_crawl(title_list):
            return
        movie_data_proto = copy.deepcopy(data_proto)
        movie_data_proto['title'] = title
        showing_section_list = curr_movie.xpath(
            './/td[contains(@onmouseover,"eventover")]')
        for curr_showing in showing_section_list:
            self.parse_showing(response, curr_showing,
                               movie_data_proto, result_list)

    def parse_showing(self, response, curr_showing, data_proto, result_list):
        def parse_time(time_str):
            time = time_str.split(":")
            return (int(time[0]), int(time[1]))
        print("parse_showing")

        showing_data_proto = copy.deepcopy(data_proto)
        screen_name = curr_showing.xpath('./p/text()').extract_first()
        showing_data_proto['screen'] = standardize_screen_name(
            screen_name, showing_data_proto['cinema_name'])
        start_time = curr_showing.xpath(
            './/span[@class="strong fontXL"]/text()').extract_first()
        start_hour, start_minute = parse_time(start_time)
        showing_data_proto['start_time'] = self.get_time_from_text(
            start_hour, start_minute)
        end_time = curr_showing.xpath(
            './/span[@class="strong fontXL"]/../text()').extract_first()[1:]
        end_hour, end_minute = parse_time(end_time)
        showing_data_proto['end_time'] = self.get_time_from_text(
            end_hour, end_minute)
        # TEST
        print(showing_data_proto['screen'])
        print(showing_data_proto['start_time'])
        print(showing_data_proto['end_time'])
        return
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
