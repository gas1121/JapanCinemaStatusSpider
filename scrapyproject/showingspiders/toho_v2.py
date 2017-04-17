# -*- coding: utf-8 -*-
import unicodedata
import json
import copy
import arrow
import scrapy
from scrapyproject.showingspiders.showing_spider import ShowingSpider
from scrapyproject.items import (ShowingItem, ShowingBookingItem,
                                 standardize_cinema_name,
                                 standardize_screen_name)
from scrapyproject.models import Cinema
from scrapyproject.utils import standardize_site_url, TohoUtil


class TohoV2Spider(ShowingSpider):
    """
    Toho site spider version 2.

    Improve crawling speed as we grab data from json api instead of site page.

    useful json api:
    theater list:
    https://hlo.tohotheater.jp/responsive/json/theater_list.json?_dc=1488106193
    movies showing now:
    https://hlo.tohotheater.jp/data_net/json/movie/TNPI3090.JSON
    movies coming soon:
    https://hlo.tohotheater.jp/data_net/json/movie/TNPI3080.JSON
    time schedule table:
    https://hlo.tohotheater.jp/net/schedule/TNPI3070J02.do?
    __type__=json&movie_cd=014174&vg_cd=028&term=99&seq_disp_term=7
    &site_cd=&enter_kbn=&_dc=1488106557
    detail schedule table for movie:
    https://hlo.tohotheater.jp/net/schedule/TNPI3070J01.do?
    __type__=json&movie_cd=014174&vg_cd=028&show_day=20170226
    &term=99&isMember=&site_cd=028&enter_kbn=&_dc=1488106558
    cinema schedult table:
    https://hlo.tohotheater.jp/net/schedule/TNPI3050J02.do?
    __type__=html&__useResultInfo__=no&vg_cd=076&show_day=20170226
    &term=99&isMember=&enter_kbn=&_dc=1488120297

    Visit page example:
    https://www.tohotheater.jp/theater/find.html
    https://hlo.tohotheater.jp/net/movie/TNPI3090J01.do
    https://hlo.tohotheater.jp/net/movie/TNPI3060J01.do?sakuhin_cd=014174
    https://hlo.tohotheater.jp/net/ticket/034/TNPI2040J03.do

    We will first crawl cinema list, then crawl each cinema's schedule data,
    and generate booking page urls to crawl exact booking number
    """
    name = "toho_v2"
    allowed_domains = ["hlo.tohotheater.jp", "www.tohotheater.jp"]
    start_urls = [
        'https://hlo.tohotheater.jp/responsive/json/theater_list.json'
    ]

    cinema_list = ['TOHOシネマズ 新宿']

    def parse(self, response):
        """
        crawl theater list data first
        """
        try:
            theater_list = json.loads(response.text)
        except json.JSONDecodeError:
            return
        if (not theater_list):
            return
        for curr_cinema in theater_list:
            cinema_name_list = self.get_cinema_name_list(curr_cinema)
            if not self.is_cinema_crawl(cinema_name_list):
                continue
            site_cd = curr_cinema['VIT_GROUP_CD']
            show_day = self.date
            curr_cinema_url = self.generate_cinema_schedule_url(
                site_cd, show_day)
            request = scrapy.Request(curr_cinema_url,
                                     callback=self.parse_cinema)
            yield request

    def get_cinema_name_list(self, curr_cinema):
        # replace full width text before compare
        vit_group_nm = unicodedata.normalize('NFKC',
                                             curr_cinema['VIT_GROUP_NM'])
        theater_name = unicodedata.normalize('NFKC',
                                             curr_cinema['THEATER_NAME'])
        theater_name_english = unicodedata.normalize(
            'NFKC', curr_cinema['THEATER_NAME_ENGLISH'])
        site_name = unicodedata.normalize('NFKC', curr_cinema['SITE_NM'])
        return [vit_group_nm, theater_name, theater_name_english, site_name]

    def generate_cinema_schedule_url(self, site_cd, show_day):
        """
        json data url for single cinema, all movies of curr cinema
        """
        url = 'https://hlo.tohotheater.jp/net/schedule/TNPI3050J02.do?'\
              '__type__=html&__useResultInfo__=no'\
              '&vg_cd={site_cd}&show_day={show_day}&term=99'.format(
                site_cd=site_cd, show_day=show_day)
        return url

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
        site_cd = sub_cinema['code']
        showing_url_parameter['site_cd'] = site_cd
        cinema_name = sub_cinema['name']
        cinema_name = standardize_cinema_name(cinema_name)
        data_proto = ShowingItem()
        data_proto['cinema_name'] = cinema_name
        cinema_site = TohoUtil.generate_cinema_homepage_url(site_cd)
        data_proto["cinema_site"] = standardize_site_url(
            cinema_site, cinema_name)
        data_proto['source'] = self.name
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
        # normalize title_en to avoid full width characters
        title_en = unicodedata.normalize('NFKC', curr_movie['ename'])
        if not self.is_movie_crawl([title, title_en]):
            return
        showing_url_parameter['movie_cd'] = curr_movie['code']
        movie_data_proto = copy.deepcopy(data_proto)
        movie_data_proto['title'] = title
        movie_data_proto['title_en'] = title_en
        for curr_screen in curr_movie['list']:
            self.parse_screen(response, curr_screen, showing_url_parameter,
                              movie_data_proto, result_list)

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
        def parse_time(time_str):
            """
            ex. "24:40"
            """
            time = time_str.split(":")
            return (int(time[0]), int(time[1]))
        showing_url_parameter['showing_cd'] = curr_showing['code']
        showing_data_proto = copy.deepcopy(data_proto)
        # time like 24:40 can not be directly parsed,
        # so we need to shift time properly
        start_hour, start_minute = parse_time(curr_showing['showingStart'])
        showing_data_proto['start_time'] = self.get_time_from_text(
            start_hour, start_minute)
        end_hour, end_minute = parse_time(curr_showing['showingEnd'])
        showing_data_proto['end_time'] = self.get_time_from_text(
            end_hour, end_minute)
        showing_data_proto['seat_type'] = 'NormalSeat'

        # query screen number from database
        showing_data_proto['total_seat_count'] = \
            Cinema.get_screen_seat_count(
                cinema_name=showing_data_proto['cinema_name'],
                cinema_site=showing_data_proto['cinema_site'],
                screen=showing_data_proto['screen'])
        # check whether need to continue crawl booking data or stop now
        if not self.crawl_booking_data:
            result_list.append(showing_data_proto)
            return
        booking_data_proto = ShowingBookingItem()
        booking_data_proto['showing'] = showing_data_proto
        booking_data_proto['book_status'] = TohoUtil.standardize_book_status(
            curr_showing['unsoldSeatInfo']['unsoldSeatStatus'])
        if booking_data_proto['book_status'] in ['SoldOut', 'NotSold']:
            # sold out or not sold
            status = booking_data_proto['book_status']
            booking_data_proto['book_seat_count'] = (
                showing_data_proto['total_seat_count']
                if status == 'SoldOut' else 0)
            booking_data_proto['record_time'] = arrow.now()
            result_list.append(booking_data_proto)
            return
        else:
            # normal, need to crawl book number on order page
            url = self.generate_showing_url(**showing_url_parameter)
            request = scrapy.Request(url,
                                     callback=self.parse_normal_showing)
            request.meta["data_proto"] = booking_data_proto
            result_list.append(request)

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
        booked_seat_count = len(response.css('[alt~="購入済(選択不可)"]'))
        result = response.meta["data_proto"]
        result['book_seat_count'] = booked_seat_count
        result['record_time'] = arrow.now()
        time_before = result['showing']['start_time'] - result['record_time'] 
        result['minutes_before'] = (
            time_before.days*1440 + time_before.seconds//60)
        yield result
