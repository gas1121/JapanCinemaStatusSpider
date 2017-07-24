# -*- coding: utf-8 -*-
import re
import copy
from crawling.spiders.redis_spider import RedisSpider

from crawler.items import (CinemaItem, standardize_cinema_name,
                                 standardize_screen_name)
from crawler.utils import CinemaDatabaseMixin, TohoUtil


class TohoCinemaSpider(RedisSpider, CinemaDatabaseMixin):
    name = "toho_cinema"
    allowed_domains = ["hlo.tohotheater.jp", "www.tohotheater.jp"]
    #start_urls = ['https://www.tohotheater.jp/theater/find.html']

    def parse(self, response):
        """
        enter point for response process
        """
        self._logger.debug("crawled url {}".format(response.request.url))
        result_list = []
        if "curr_step" not in response.meta:
            self.parse_mainpage(response, result_list)
        else:
            curr_step = response.meta["curr_step"]
            if curr_step == "cinema":
                self.parse_cinema(response, result_list)
            else:
                self.parse_sub_cinema(response, result_list)
        for result in result_list:
            yield result

    def parse_mainpage(self, response, result_list):
        """
        crawl toho cinema info, mainly seats count of each screen
        example: https://www.tohotheater.jp/theater/064/institution.html
        https://hlo.tohotheater.jp/net/schedule/064/TNPI2000J01.do
        """
        self._logger.debug("{}: parse_mainpage in '{}'".format(
            self.name, response.url))
        all_areas = response.xpath('//h3[contains(text(),"地区")]/..')
        for curr_area in all_areas:
            all_counties = curr_area.xpath('./div//section')
            for curr_county in all_counties:
                county = curr_county.xpath('./h4/text()').extract_first()
                all_cinema_url = curr_county.xpath(
                    './/a[contains(@href,"schedule")]/@href')
                for curr_cinema_url in all_cinema_url:
                    cinema_number = curr_cinema_url.re(
                        r'/net/schedule/([0-9]+)/TNPI2000J01.do')
                    tail_url = '/theater/'+cinema_number[0]+'/institution.html'
                    cinema_site = TohoUtil.generate_cinema_homepage_url(
                        cinema_number[0])
                    request = response.follow(tail_url, callback=self.parse)
                    request.meta['curr_step'] = "cinema"
                    request.meta['county'] = county
                    request.meta['site'] = cinema_site
                    result_list.append(request)

    def parse_cinema(self, response, result_list):
        self._logger.debug("{}: parse_cinema in '{}'".format(
            self.name, response.url))
        cinema_name = response.xpath(
            '//h1[@class="c-page_heading is-lv-01"]'
            '/span/text()').extract_first()
        cinema = CinemaItem()
        cinema['names'] = [standardize_cinema_name(cinema_name)]
        cinema['screens'] = {}
        cinema['county'] = response.meta['county']
        cinema['company'] = 'TOHO'
        cinema['source'] = self.name
        cinema['site'] = response.meta['site']
        # some cinemas have detail page and need to forward
        sub_page_list = response.xpath(
            '//section[@class="about"]//a[@class="link bold"]/@href').extract()
        if sub_page_list:
            for sub_page_url in sub_page_list:
                request = response.follow(sub_page_url, callback=self.parse)
                request.meta['curr_step'] = "sub_cinema"
                # pass item by dict type
                request.meta['cinema'] = dict(copy.deepcopy(cinema))
                result_list.append(request)
        else:
            self.parse_seat_number_list(response, cinema)
            result_list.append(cinema)

    def parse_sub_cinema(self, response, result_list):
        self._logger.debug("{}: parse_sub_cinema in '{}'".format(
            self.name, response.url))
        cinema = CinemaItem(response.meta['cinema'])
        # sub cinema use its own name
        cinema_name = response.xpath(
            '//div[@id="more-anchor-01"]/h4/text()').extract_first()
        cinema['names'] = [standardize_cinema_name(cinema_name)]
        self.parse_seat_number_list(response, cinema)
        result_list.append(cinema)

    def parse_seat_number_list(self, response, cinema):
        # table on https://www.tohotheater.jp/theater/021/institution.html
        # has wrong order of <tr> and </tr> which makes parser fails to parse,
        # so we have to handle this problem manually...
        all_screen_list = response.xpath(
            '//table[contains(@class,"c-table01")]/tbody/tr')
        # except total seats line
        all_screen_list = all_screen_list[:-1]
        screen_count = 0
        total_seats = 0
        for curr_screen in all_screen_list:
            screen_name = curr_screen.xpath(
                './td[1]/text()').extract_first()
            # empty row may exist
            if screen_name is not None:
                screen_name = standardize_screen_name(
                    screen_name, cinema['names'][0])
                screen_seat_number_list = curr_screen.xpath(
                    './td[2]/text()').re(r'([0-9]+)[\+\＋]\(([0-9]+)\)')
                screen_seat_number = (int(screen_seat_number_list[0])
                                      + int(screen_seat_number_list[1]))
                screen_count += 1
                total_seats += screen_seat_number
                cinema['screens'][screen_name] = screen_seat_number
        # screen_count<2 means we have problem crawling data
        if screen_count < 2:
            tbody_text = response.xpath(
                '//table[contains(@class,"c-table01")]/tbody').extract_first()
            screen_list = re.findall(r'<td>(SCREEN.*)</td>', tbody_text)
            seat_list = re.findall(r'<td>(\d+)\+\((\d+)\)', tbody_text)
            screen_count = 0
            total_seats = 0
            cinema['screens'] = {}
            for screen_name, seats in zip(screen_list, seat_list):
                curr_seat_count = int(seats[0]) + int(seats[1])
                cinema['screens'][screen_name] = curr_seat_count
                screen_count += 1
                total_seats += curr_seat_count
        cinema['screen_count'] = screen_count
        cinema['total_seats'] = total_seats
