# -*- coding: utf-8 -*-
import datetime
import unicodedata
import scrapy
from scrapyproject.items import (Session, standardize_cinema_name,
                                 standardize_screen_name)
from scrapyproject.models import query_cinema_by_name


class TohoSpider(scrapy.Spider):
    name = "toho"
    allowed_domains = ["hlo.tohotheater.jp", "www.tohotheater.jp"]
    start_urls = ['https://www.tohotheater.jp/theater/find.html']

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
        config = {}
        self.set_config(config)
        cinema_page_url_list = []
        if config['crawl_all_cinemas']:
            cinema_page_url_list = response.xpath(
                '//a[contains(@href,"schedule")]/@href').extract()
        else:
            for curr_cinema in config['cinema_list']:
                cinema_page_url = response.xpath(
                    '//a[span[contains(text(),"' + curr_cinema +
                    '")]]/@href').extract_first()
                cinema_page_url_list.append(cinema_page_url)
        for curr_page_url in cinema_page_url_list:
            cinema_page_url = response.urljoin(curr_page_url)
            request = scrapy.Request(cinema_page_url,
                                     callback=self.parse_cinema)
            request.meta["crawl_all_movies"] = config['crawl_all_movies']
            request.meta["selectDate"] = config['date']
            request.meta["movie_list"] = config['movie_list']
            yield request

    def parse_cinema(self, response):
        # multiple cinema names may exist in one page
        sub_cinema_list = response.xpath(
            '//section[@class="schedule-body-section"]')
        result_list = []
        for sub_cinema in sub_cinema_list:
            self.parse_sub_cinema(response, sub_cinema, result_list)
        for result in result_list:
            if result:
                yield result

    def parse_sub_cinema(self, response, sub_cinema, result_list):
        cinema_name = sub_cinema.xpath('./h4/text()').extract_first()
        cinema_name = standardize_cinema_name(cinema_name)
        movie_section_list = sub_cinema.xpath('./div')
        for movie_section in movie_section_list:
            self.parse_movie_section(
                response, movie_section, cinema_name, result_list)

    def parse_movie_section(self, response, movie_section,
                            cinema_name, result_list):
        # title keep origin string
        title = movie_section.xpath('./div/h5/text()').extract_first()
        title_en = movie_section.xpath(
            './/div[@class="en"]/text()').extract_first()
        # normalize title_en to avoid full width characters
        title_en = unicodedata.normalize('NFKC', title_en)
        if not response.meta["crawl_all_movies"]:
            # if not crawl all movies, test if input title is contained
            title_contained = any(curr_title in title for curr_title
                                  in response.meta["movie_list"])
            title_en_contained = any(curr_title in title_en for curr_title
                                     in response.meta["movie_list"])
            if ((not title_contained) and (not title_en_contained)):
                return
        # handle all sessions, include sold out and outdated sessions
        all_screens = movie_section.xpath(
            './/section[@class="schedule-screen"]')
        for curr_screen in all_screens:
            self.parse_screen(response, curr_screen, cinema_name,
                              title, title_en, result_list)

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

    def parse_normal_session(self, response):
        empty_seat_count = len(response.css('[alt~="空席(選択可)"]'))
        booked_seat_count = len(response.css('[alt~="購入済(選択不可)"]'))
        total_seat_count = empty_seat_count + booked_seat_count
        result = response.meta["crawl_data"]
        result['book_seat_count'] = booked_seat_count
        result['total_seat_count'] = total_seat_count
        result['record_time'] = datetime.datetime.now()
        yield result
