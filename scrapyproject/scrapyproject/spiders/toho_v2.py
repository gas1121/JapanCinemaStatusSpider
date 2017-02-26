# -*- coding: utf-8 -*-
import datetime
import unicodedata
import json
import scrapy
from scrapyproject.items import (Session, standardize_cinema_name,
                                 standardize_screen_name)
from scrapyproject.models import query_cinema_by_name


class TohoV2Spider(scrapy.Spider):
    """
    Toho site spider version 2.

    Improve crawling speed as we grab data from json api instead of real page
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
            True if hasattr(self, 'crawl_all_cinemas') else True)
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
        theater_list = json.loads(response.text)
        if (not theater_list):
            return
        for curr_cinema in theater_list:
            if not self.is_cinema_crawl(curr_cinema, config['cinema_list'],
                                        config['crawl_all_cinemas']):
                continue
            site_cd = curr_cinema['SITE_CD']
            show_day = config['date'].strftime("%Y%m%d")
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
        if (curr_cinema['VIT_GROUP_NM'] in cinema_list or
                curr_cinema['THEATER_NAME'] in cinema_list or
                curr_cinema['THEATER_NAME_ENGLISH'] in cinema_list or
                curr_cinema['SITE_NM'] in cinema_list):
                return True
        return False

    def generate_cinema_schedule_url(self, site_cd, show_day):
        """
        json data url for single cinema, all movies of curr cinema
        """
        url = 'https://hlo.tohotheater.jp/net/'
        'schedule/TNPI3050J02.do?__type__=html&__useResultInfo__=no'
        '&vg_cd={site_cd}&show_day={show_day}&term=99'.format(
            site_cd=site_cd, show_day=show_day)
        return url

    def parse_cinema(self, response):
        schedule_data = json.loads(response.text)
        if (not schedule_data):
            return
        for curr_cinema in schedule_data:
            for sub_cinema in curr_cinema['list']:
                cinema_name = sub_cinema['name']
                cinema_name = standardize_cinema_name(cinema_name)
                for curr_movie in sub_cinema['list']:
                    # movie may have different versions
                    title = curr_movie['name']
                    title_en = curr_movie['ename']
                    # normalize title_en to avoid full width characters
                    title_en = unicodedata.normalize('NFKC', title_en)
                    if not self.is_movie_crawl(
                        title, title_en, response.meta["movie_list"],
                            response.meta["crawl_all_movies"]):
                        continue
                        # TODO

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

    def generate_session_url(self, curr_session_url_item):
        # example: javascript:ScheduleUtils.purchaseTicket(
        #  "20170212", "076", "013132", "0761", "11", "2")
        # example: https://hlo.tohotheater.jp/net/ticket/076/TNPI2040J03.do
        # ?site_cd=076&jyoei_date=20170209&gekijyo_cd=0761&screen_cd=10
        # &sakuhin_cd=014183&pf_no=5&fnc=1&pageid=2000J01&enter_kbn=
        parameters = curr_session_url_item.re(r'purchaseTicket\("([0-9]+)", '
                                              '"([0-9]+)", "([0-9]+)", '
                                              '"([0-9]+)", "([0-9]+)", '
                                              '"([0-9]+)"\)')
        return "https://hlo.tohotheater.jp/net/ticket/{site_cd}/"\
               "TNPI2040J03.do?site_cd={site_cd}&jyoei_date={jyoei_date}"\
               "&gekijyo_cd={gekijyo_cd}&screen_cd={screen_cd}"\
               "&sakuhin_cd={sakuhin_cd}&pf_no={pf_no}&fnc={fnc}"\
               "&pageid={pageid}&enter_kbn={enter_kbn}".format(
                   site_cd=parameters[1], jyoei_date=parameters[0],
                   gekijyo_cd=parameters[3], screen_cd=parameters[4],
                   sakuhin_cd=parameters[2], pf_no=parameters[5],
                   fnc="1", pageid="2000J01", enter_kbn="")


    def parse_screen(self, response, curr_screen, cinema_name,
                     title, title_en, result_list):
        crawl_data = Session()
        crawl_data['cinema_name'] = cinema_name
        crawl_data['title'] = title
        crawl_data['title_en'] = title_en
        crawl_data['screen'] = curr_screen.xpath(
            './h5[@class="schedule-screen-title"]/text()').extract_first()
        # make sure screen name is same with those in cinemas table
        crawl_data['screen'] = standardize_screen_name(
            crawl_data['screen'], crawl_data['cinema_name'])
        screen_sessions = curr_screen.xpath(
            './/div[@class="schedule-items group"]/div')
        for curr_session in screen_sessions:
            # time like 24:40 can not directly parsed by datetime,
            # so we need to use timedelta to handle this problem
            start_time_text = curr_session.xpath(
                './/span[@class="start"]/text()').extract_first()
            crawl_data['start_time'] = self.get_time_from_text(
                response, start_time_text)
            end_time_text = curr_session.xpath(
                './/span[@class="end"]/text()').extract_first()
            crawl_data['end_time'] = self.get_time_from_text(
                response, end_time_text)
            result = self.parse_session(crawl_data, curr_session)
            result_list.append(result)

    def get_time_from_text(self, response, time_text):
        """
        generate datetime object from response and extracted time text
        """
        time_list = time_text.split(':')
        hours = int(time_list[0])
        minutes = int(time_list[1])
        time_delta = datetime.timedelta(hours=hours, minutes=minutes)
        time = datetime.datetime.strptime(response.meta["selectDate"],
                                          "%Y%m%d")+time_delta
        return time

    def parse_session(self, crawl_data, curr_session):
        crawl_data['book_status'] = curr_session.xpath(
                './/p[contains(@class,"status")]/text()').extract_first()
        if (curr_session.xpath('./@class').extract_first()
                == 'schedule-item white'):
            # normal
            session_url = curr_session.xpath('./a/@href')
            url = self.generate_session_url(session_url)
            request = scrapy.Request(url,
                                     callback=self.parse_normal_session)
            request.meta["crawl_data"] = crawl_data.copy()
            return request
        else:
            if crawl_data['book_status'] == "売り切れ":
                # sold out
                cinema_name = crawl_data['cinema_name']
                cinema = query_cinema_by_name(cinema_name)
                if cinema:
                    if crawl_data['screen'] in cinema.screens:
                        crawl_data['book_seat_count'] = cinema.screens[
                            crawl_data['screen']]
                        crawl_data['total_seat_count'] = cinema.screens[
                            crawl_data['screen']]
                    else:
                        crawl_data['book_seat_count'] = 0
                        crawl_data['total_seat_count'] = 0
                else:
                    crawl_data['book_seat_count'] = 0
                    crawl_data['total_seat_count'] = 0
            else:
                # outdated
                crawl_data['book_seat_count'] = 0
                crawl_data['total_seat_count'] = 0
            crawl_data['record_time'] = datetime.datetime.now()
            return crawl_data.copy()

    def parse_normal_session(self, response):
        empty_seat_count = len(response.css('[alt~="空席(選択可)"]'))
        booked_seat_count = len(response.css('[alt~="購入済(選択不可)"]'))
        total_seat_count = empty_seat_count + booked_seat_count
        result = response.meta["crawl_data"]
        result['book_seat_count'] = booked_seat_count
        result['total_seat_count'] = total_seat_count
        result['record_time'] = datetime.datetime.now()
        yield result
