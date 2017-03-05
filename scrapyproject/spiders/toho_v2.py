# -*- coding: utf-8 -*-
import datetime
import unicodedata
import json
import copy
import scrapy
from scrapyproject.items import (Session, standardize_cinema_name,
                                 standardize_screen_name)
from scrapyproject.models import query_cinema_by_name
from scrapyproject.utils.spider_helper import CinemasDatabaseMixin


class TohoV2Spider(scrapy.Spider, CinemasDatabaseMixin):
    """
    Toho site spider version 2.

    Improve crawling speed as we grab data from json api instead of site page
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

    def set_config(self, config):
        """
        only movie title are raw str, others are normailized
        """
        config['movie_list'] = getattr(self, 'movie_list', ['君の名は。'])
        if not isinstance(config['movie_list'], list):
            config['movie_list'] = config['movie_list'].split(',')
        # scrapy doesn't allow to pass name without value
        config['crawl_all_movies'] = (
            True if hasattr(self, 'crawl_all_movies') else False)
        config['crawl_all_cinemas'] = (
            True if hasattr(self, 'crawl_all_cinemas') else False)
        config['cinema_list'] = getattr(self, 'cinema_list',
                                        ['TOHOシネマズ 新宿'])
        if not isinstance(config['cinema_list'], list):
            config['cinema_list'] = config['cinema_list'].split(',')
        # should not remove space, but normalize only
        for idx, item in enumerate(config['cinema_list']):
            config['cinema_list'][idx] = unicodedata.normalize('NFKC', item)
        # date: default tomorrow
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        config['date'] = getattr(self, 'date', '{:02d}{:02d}{:02d}'.format(
            tomorrow.year, tomorrow.month, tomorrow.day))

    def parse(self, response):
        """
        crawl theater list data first
        """
        config = {}
        self.set_config(config)
        try:
            theater_list = json.loads(response.text)
        except json.JSONDecodeError:
            return
        if (not theater_list):
            return
        for curr_cinema in theater_list:
            if not self.is_cinema_crawl(curr_cinema, config['cinema_list'],
                                        config['crawl_all_cinemas']):
                continue
            site_cd = curr_cinema['VIT_GROUP_CD']
            show_day = config['date']
            curr_cinema_url = self.generate_cinema_schedule_url(
                site_cd, show_day)
            request = scrapy.Request(curr_cinema_url,
                                     callback=self.parse_cinema)
            request.meta["crawl_all_movies"] = config['crawl_all_movies']
            request.meta["movie_list"] = config['movie_list']
            yield request

    def is_cinema_crawl(self, curr_cinema, cinema_list, crawl_all_cinemas):
        """
        check if current cinema should be crawled
        """
        if crawl_all_cinemas:
            return True
        # replace full width text before compare
        vit_group_nm = unicodedata.normalize('NFKC', 
                                             curr_cinema['VIT_GROUP_NM'])
        theater_name = unicodedata.normalize('NFKC', 
                                             curr_cinema['THEATER_NAME'])
        theater_name_english = unicodedata.normalize(
            'NFKC', curr_cinema['THEATER_NAME_ENGLISH'])
        site_name = unicodedata.normalize('NFKC', curr_cinema['SITE_NM'])
        if (vit_group_nm in cinema_list or theater_name in cinema_list
            or theater_name_english in cinema_list
                or site_name in cinema_list):
                return True
        return False

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
        # some cinemas may not open currently and will return empty response
        try:
            schedule_data = json.loads(response.text)
        except json.JSONDecodeError:
            return
        if (not schedule_data):
            return
        result_list = []
        for curr_cinema in schedule_data:
            session_url_parameter = {}
            session_url_parameter['show_day'] = curr_cinema['showDay']['date']
            for sub_cinema in curr_cinema['list']:
                self.parse_sub_cinema(
                    response, sub_cinema, session_url_parameter, result_list)
        for result in result_list:
            if result:
                yield result

    def parse_sub_cinema(self, response, sub_cinema,
                         session_url_parameter, result_list):
        session_url_parameter['site_cd'] = sub_cinema['code']
        cinema_name = sub_cinema['name']
        cinema_name = standardize_cinema_name(cinema_name)
        data_proto = Session()
        data_proto['cinema_name'] = cinema_name
        for curr_movie in sub_cinema['list']:
            self.parse_movie(response, curr_movie, session_url_parameter,
                             data_proto, result_list)

    def parse_movie(self, response, curr_movie,
                    session_url_parameter, data_proto, result_list):
        """
        parse movie session data
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
        session_url_parameter['movie_cd'] = curr_movie['code']
        movie_data_proto = copy.deepcopy(data_proto)
        movie_data_proto['title'] = title
        movie_data_proto['title_en'] = title_en
        for curr_screen in curr_movie['list']:
            self.parse_screen(response, curr_screen, session_url_parameter,
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
                     session_url_parameter, data_proto, result_list):
        screen = curr_screen['ename']
        session_url_parameter['theater_cd'] = curr_screen['theaterCd']
        session_url_parameter['screen_cd'] = curr_screen['code']
        screen_data_proto = copy.deepcopy(data_proto)
        # make sure screen name is same with those in cinemas table
        screen_data_proto['screen'] = standardize_screen_name(
            screen, screen_data_proto['cinema_name'])
        for curr_session in curr_screen['list']:
            # filter empty session
            if not curr_session['unsoldSeatInfo']:
                continue
            self.parse_session(response, curr_session, session_url_parameter,
                               screen_data_proto, result_list)

    def parse_session(self, response, curr_session,
                      session_url_parameter, data_proto, result_list):
        session_url_parameter['session_cd'] = curr_session['code']
        session_data_proto = copy.deepcopy(data_proto)
        # time like 24:40 can not directly parsed by datetime,
        # so we need to use timedelta to handle this problem
        session_data_proto['start_time'] = self.get_time_from_text(
            session_url_parameter['show_day'], curr_session['showingStart']
        )
        session_data_proto['end_time'] = self.get_time_from_text(
            session_url_parameter['show_day'], curr_session['showingEnd']
        )
        session_data_proto['book_status'] = curr_session[
            'unsoldSeatInfo']['unsoldSeatStatus']
        # status:
        # A Plenty Left
        # B Half full
        # C Few Seats Left
        # D Sold Out
        # G Not Sold
        if session_data_proto['book_status'] == 'D':
            # sold out
            cinema_name = data_proto['cinema_name']
            cinema = query_cinema_by_name(cinema_name)
            if cinema:
                if session_data_proto['screen'] in cinema.screens:
                    session_data_proto['book_seat_count'] = cinema.screens[
                        session_data_proto['screen']]
                    session_data_proto['total_seat_count'] = cinema.screens[
                        session_data_proto['screen']]
                else:
                    session_data_proto['book_seat_count'] = 0
                    session_data_proto['total_seat_count'] = 0
            else:
                session_data_proto['book_seat_count'] = 0
                session_data_proto['total_seat_count'] = 0
            session_data_proto['record_time'] = datetime.datetime.now()
            result_list.append(session_data_proto)
            return
        elif session_data_proto['book_status'] == 'G':
            # not sold
            session_data_proto['book_seat_count'] = 0
            session_data_proto['total_seat_count'] = 0
            session_data_proto['record_time'] = datetime.datetime.now()
            result_list.append(session_data_proto)
            return
        else:
            # normal, need to crawl book number on order page
            url = self.generate_session_url(session_url_parameter)
            request = scrapy.Request(url,
                                     callback=self.parse_normal_session)
            request.meta["data_proto"] = session_data_proto
            result_list.append(request)

    def get_time_from_text(self, show_day, time_text):
        """
        generate datetime object from given day and time text

        as time like 24:40 can not directly parsed by datetime,
        so we need to use timedelta to handle this problem
        """
        time_list = time_text.split(':')
        hours = int(time_list[0])
        minutes = int(time_list[1])
        time_delta = datetime.timedelta(hours=hours, minutes=minutes)
        time = datetime.datetime.strptime(show_day, "%Y%m%d")+time_delta
        return time

    def generate_session_url(self, session_url_parameter):
        # example: javascript:ScheduleUtils.purchaseTicket(
        #  "20170212", "076", "013132", "0761", "11", "2")
        # example: https://hlo.tohotheater.jp/net/ticket/076/TNPI2040J03.do
        # ?site_cd=076&jyoei_date=20170209&gekijyo_cd=0761&screen_cd=10
        # &sakuhin_cd=014183&pf_no=5&fnc=1&pageid=2000J01&enter_kbn=
        site_cd = session_url_parameter['site_cd']
        show_day = session_url_parameter['show_day']
        theater_cd = session_url_parameter['theater_cd']
        screen_cd = session_url_parameter['screen_cd']
        movie_cd = session_url_parameter['movie_cd']
        session_cd = session_url_parameter['session_cd']
        return "https://hlo.tohotheater.jp/net/ticket/{site_cd}/"\
               "TNPI2040J03.do?site_cd={site_cd}&jyoei_date={jyoei_date}"\
               "&gekijyo_cd={gekijyo_cd}&screen_cd={screen_cd}"\
               "&sakuhin_cd={sakuhin_cd}&pf_no={pf_no}&fnc={fnc}"\
               "&pageid={pageid}&enter_kbn={enter_kbn}".format(
                   site_cd=site_cd, jyoei_date=show_day,
                   gekijyo_cd=theater_cd, screen_cd=screen_cd,
                   sakuhin_cd=movie_cd, pf_no=session_cd,
                   fnc="1", pageid="2000J01", enter_kbn="")

    def parse_normal_session(self, response):
        empty_seat_count = len(response.css('[alt~="空席(選択可)"]'))
        booked_seat_count = len(response.css('[alt~="購入済(選択不可)"]'))
        total_seat_count = empty_seat_count + booked_seat_count
        result = response.meta["data_proto"]
        result['book_seat_count'] = booked_seat_count
        result['total_seat_count'] = total_seat_count
        result['record_time'] = datetime.datetime.now()
        yield result
