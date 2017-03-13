# -*- coding: utf-8 -*-
import unicodedata
import json
import copy
import arrow
import scrapy
from scrapyproject.spiders.showing_spider import ShowingSpider
from scrapyproject.items import (Showing, standardize_cinema_name,
                                 standardize_screen_name)
from scrapyproject.utils.site_utils import standardize_book_status


class CinemaSunshineSpider(ShowingSpider):
    """
    Cinema Sunshine spider.
    """
    name = "cinemasunshine"
    allowed_domains = ["www.cinemasunshine.co.jp", "www2.css-ebox.jp"]
    start_urls = [
        'http://www.cinemasunshine.co.jp/theater/'
    ]

    def parse(self, response):
        """
        crawl theater list data first
        """
        config = {}
        self.set_config(config)
        theater_list = response.xpath('//li[@class="clearfix"]')
        for theater_element in theater_list:
            cinema_names = theater_element.xpath(
                './p[@class="theaterName"]/a/text()').extract()
            if not self.is_cinema_crawl(cinema_names, config):
                continue
            county = theater_element.xpath(
                './p[@class="theaterPracce"]/text()').extract_first()
            curr_cinema_url = theater_element.xpath(
                './p[@class="theaterName"]/a/@href').extract_first()
            curr_cinema_url = response.urljoin(curr_cinema_url)
            request = scrapy.Request(curr_cinema_url,
                                     callback=self.parse_cinema)
            request.meta["county"] = county
            request.meta["conifg"] = config
            yield request

    def parse_cinema(self, response):
        # some cinemas may not open and will return empty response
        try:
            schedule_data = json.loads(response.text)
        except json.JSONDecodeError:
            return
        if (not schedule_data):
            return
        result_list = []
        for curr_cinema in schedule_data:
            showing_url_parameter = {}
            date_str = curr_cinema['showDay']['date']
            showing_url_parameter['show_day'] = arrow.get(
                date_str, 'YYYYMMDD').replace(tzinfo='UTC+9')
            for sub_cinema in curr_cinema['list']:
                self.parse_sub_cinema(
                    response, sub_cinema, showing_url_parameter, result_list)
        for result in result_list:
            if result:
                yield result

    def parse_sub_cinema(self, response, sub_cinema,
                         showing_url_parameter, result_list):
        showing_url_parameter['site_cd'] = sub_cinema['code']
        cinema_name = sub_cinema['name']
        cinema_name = standardize_cinema_name(cinema_name)
        data_proto = Showing()
        data_proto['cinema_name'] = cinema_name
        # TODO site is not correct
        data_proto['cinema_site'] = response.url.split("?")[0]
        for curr_movie in sub_cinema['list']:
            self.parse_movie(response, curr_movie, showing_url_parameter,
                             data_proto, result_list)

    def parse_movie(self, response, curr_movie,
                    showing_url_parameter, data_proto, result_list):
        """
        parse movie showing data
        movie may have different versions
        """
        title = curr_movie['name']
        title_en = curr_movie['ename']
        # normalize title_en to avoid full width characters
        title_en = unicodedata.normalize('NFKC', title_en)
        if not self.is_movie_crawl(
            title, title_en, response.meta["movie_list"],
                response.meta["crawl_all_movies"]):
            return
        showing_url_parameter['movie_cd'] = curr_movie['code']
        movie_data_proto = copy.deepcopy(data_proto)
        movie_data_proto['title'] = title
        movie_data_proto['title_en'] = title_en
        for curr_screen in curr_movie['list']:
            self.parse_screen(response, curr_screen, showing_url_parameter,
                              movie_data_proto, result_list)

    def is_movie_crawl(self, title, title_en, movie_list, crawl_all_movies):
        """
        check if current movie should be crawled
        """
        if crawl_all_movies:
            return True
        # if not crawl all movies, check if input title is contained
        title_contained = any(curr_title in title for curr_title in movie_list)
        title_en_contained = any(curr_title in title_en for curr_title
                                 in movie_list)
        if (title_contained or title_en_contained):
            return True
        return False

    def parse_screen(self, response, curr_screen,
                     showing_url_parameter, data_proto, result_list):
        screen = curr_screen['ename']
        showing_url_parameter['theater_cd'] = curr_screen['theaterCd']
        showing_url_parameter['screen_cd'] = curr_screen['code']
        screen_data_proto = copy.deepcopy(data_proto)
        # make sure screen name is same with those in cinemas table
        screen_data_proto['screen'] = standardize_screen_name(
            screen, screen_data_proto['cinema_name'])
        for curr_showing in curr_screen['list']:
            # filter empty showing
            if not curr_showing['unsoldSeatInfo']:
                continue
            self.parse_showing(response, curr_showing, showing_url_parameter,
                               screen_data_proto, result_list)

    def parse_showing(self, response, curr_showing,
                      showing_url_parameter, data_proto, result_list):
        showing_url_parameter['showing_cd'] = curr_showing['code']
        showing_data_proto = copy.deepcopy(data_proto)
        # time like 24:40 can not be directly parsed,
        # so we need to shift time properly
        showing_data_proto['start_time'] = self.get_time_from_text(
            showing_url_parameter['show_day'], curr_showing['showingStart']
        )
        showing_data_proto['end_time'] = self.get_time_from_text(
            showing_url_parameter['show_day'], curr_showing['showingEnd']
        )
        showing_data_proto['book_status'] = standardize_book_status(
            curr_showing['unsoldSeatInfo']['unsoldSeatStatus'])
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
            url = self.generate_showing_url(**showing_url_parameter)
            request = scrapy.Request(url,
                                     callback=self.parse_normal_showing)
            request.meta["data_proto"] = showing_data_proto
            result_list.append(request)

    def get_time_from_text(self, show_day, time_text):
        """
        generate arrow object from given day and time text

        as time like 24:40 can not be directly parsed, we need shift time
        properly

        :param show_day: arrow object represent of 00:00 at show day.
        :param time_text: text contains time like '24:40'
        """
        time_list = time_text.split(':')
        hours = int(time_list[0])
        minutes = int(time_list[1])
        time = show_day.shift(hours=hours, minutes=minutes)
        return time

    def generate_showing_url(self, site_cd, show_day, theater_cd, screen_cd,
                             movie_cd, showing_cd):
        """
        generate showing url from given data

        :param show_day: arrow object
        """
        # example: javascript:ScheduleUtils.purchaseTicket(
        #  "20170212", "076", "013132", "0761", "11", "2")
        # example: https://hlo.tohotheater.jp/net/ticket/076/TNPI2040J03.do
        # ?site_cd=076&jyoei_date=20170209&gekijyo_cd=0761&screen_cd=10
        # &sakuhin_cd=014183&pf_no=5&fnc=1&pageid=2000J01&enter_kbn=
        day_str = show_day.format('YYYYMMDD')
        return "https://hlo.tohotheater.jp/net/ticket/{site_cd}/"\
               "TNPI2040J03.do?site_cd={site_cd}&jyoei_date={jyoei_date}"\
               "&gekijyo_cd={gekijyo_cd}&screen_cd={screen_cd}"\
               "&sakuhin_cd={sakuhin_cd}&pf_no={pf_no}&fnc={fnc}"\
               "&pageid={pageid}&enter_kbn={enter_kbn}".format(
                   site_cd=site_cd, jyoei_date=day_str,
                   gekijyo_cd=theater_cd, screen_cd=screen_cd,
                   sakuhin_cd=movie_cd, pf_no=showing_cd,
                   fnc="1", pageid="2000J01", enter_kbn="")

    def parse_normal_showing(self, response):
        empty_seat_count = len(response.css('[alt~="空席(選択可)"]'))
        booked_seat_count = len(response.css('[alt~="購入済(選択不可)"]'))
        total_seat_count = empty_seat_count + booked_seat_count
        result = response.meta["data_proto"]
        result['book_seat_count'] = booked_seat_count
        result['total_seat_count'] = total_seat_count
        result['record_time'] = arrow.now()
        result['source'] = self.name
        yield result
