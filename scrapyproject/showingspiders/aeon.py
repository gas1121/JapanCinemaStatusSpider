# -*- coding: utf-8 -*-
import re
import unicodedata
import copy
import demjson
import arrow
import scrapy
from scrapyproject.showingspiders.showing_spider import ShowingSpider
from scrapyproject.items import (Showing, standardize_cinema_name,
                                 standardize_screen_name)
from scrapyproject.utils.site_utils import AeonUtil


class AeonSpider(ShowingSpider):
    """
    aeon spider.
    """
    name = "aeon"
    allowed_domains = ["www.aeoncinema.com", "cinema.aeoncinema.com"]
    start_urls = [
        'http://www.aeoncinema.com/theater/'
    ]

    cinema_list = ['イオンシネマ板橋']

    def parse(self, response):
        """
        crawl theater list data first
        """
        theater_link_list = response.xpath(
            '//div[@class="bot clearfix"]//a')
        for theater_link in theater_link_list:
            # forum site have multiple cinema on one site, so we need to
            # specify cinema name on schedule page
            city_name = theater_link.xpath('./text()').extract_first()
            cinema_name = "イオンシネマ"+city_name
            cinema_name = standardize_cinema_name(cinema_name)
            if not self.is_cinema_crawl([cinema_name]):
                continue
            curr_cinema_url = theater_link.xpath('./@href').extract_first()
            curr_cinema_url = response.urljoin(curr_cinema_url)
            request = scrapy.Request(curr_cinema_url,
                                     callback=self.parse_cinema)
            request.meta["cinema_name"] = cinema_name
            request.meta["cinema_site"] = curr_cinema_url
            yield request

    def parse_cinema(self, response):
        """
        get schedule page from cinema site
        """
        schedule_url = response.xpath(
            '//a[contains(@href,"' + self.date + '")]/@href').extract_first()
        request = scrapy.Request(schedule_url,
                                 callback=self.parse_cinema_schedule)
        request.meta["cinema_name"] = response.meta['cinema_name']
        request.meta["cinema_site"] = response.meta['cinema_site']
        yield request

    def parse_cinema_schedule(self, response):
        data_proto = Showing()
        data_proto['cinema_name'] = response.meta['cinema_name']
        data_proto["cinema_site"] = response.meta['cinema_site']
        result_list = []
        movie_section_list = response.xpath(
            '//div[contains(@class,"movielist")]')
        for curr_movie in movie_section_list:
            self.parse_movie(response, curr_movie, data_proto, result_list)
        for result in result_list:
            if result:
                yield result

    def parse_movie(self, response, curr_movie, data_proto, result_list):
        """
        parse movie showing data
        """
        title = curr_movie.xpath('./div[1]/p[1]/a[1]/text()').extract_first()
        title = title.strip()
        title_en = curr_movie.xpath(
            './div[1]/p[1]/span/text()').extract_first()
        title_list = [title, title_en]
        if not self.is_movie_crawl(title_list):
            return
        movie_data_proto = copy.deepcopy(data_proto)
        movie_data_proto['title'] = title
        movie_data_proto['title_en'] = title_en
        show_section_list = curr_movie.xpath(
            './div[2]/div')
        for curr_showing in show_section_list:
            self.parse_showing(response, curr_showing,
                               movie_data_proto, result_list)

    def parse_showing(self, response, curr_showing, data_proto, result_list):
        def parse_time(time_str):
            time = time_str.split(":")
            return (int(time[0]), int(time[1]))

        # showing section passed in may be unusable and need to be filtered
        time_section = curr_showing.xpath('./div[@class="time"]')
        if not time_section:
            return
        showing_data_proto = copy.deepcopy(data_proto)
        start_time = time_section.xpath('./span/span/text()').extract_first()
        start_time = unicodedata.normalize('NFKC', start_time)
        start_hour, start_minute = parse_time(start_time)
        showing_data_proto['start_time'] = self.get_time_from_text(
            start_hour, start_minute)
        end_time = time_section.xpath('./span/text()').extract_first()
        end_time = unicodedata.normalize('NFKC', end_time)[1:]
        end_hour, end_minute = parse_time(end_time)
        showing_data_proto['end_time'] = self.get_time_from_text(
            end_hour, end_minute)
        screen_name = curr_showing.xpath(
            './div[@class="screen"]/a/text()').extract_first()
        screen_name = standardize_screen_name(screen_name,  showing_data_proto)
        showing_data_proto['screen'] = screen_name
        showing_data_proto['seat_type'] = 'NormalSeat'
        book_status = curr_showing.xpath('./a/span/text()').extract_first()
        showing_data_proto['book_status'] = \
            AeonUtil.standardize_book_status(book_status)
        if showing_data_proto['book_status'] in ['SoldOut', 'NotSold']:
            # sold out or not sold, seat set to 0
            showing_data_proto['book_seat_count'] = 0
            showing_data_proto['total_seat_count'] = 0
            showing_data_proto['record_time'] = arrow.now()
            showing_data_proto['source'] = self.name
            result_list.append(showing_data_proto)
            return
        else:
            # normal, go to showing seat page
            request = self.generate_agreement_request(
                response=response, curr_showing=curr_showing)
            request.meta["data_proto"] = showing_data_proto
            result_list.append(request)

    def generate_agreement_request(self, response, curr_showing):
        """
        generate post request to agreement page
        """
        # extract parameter from javascript action
        script = curr_showing.xpath('./a/@href')
        # code example:
        # javascript:selectPerformance('1703211024055000603',false,true)
        performance_id, is_special, is_reserved = script.re(
            'selectPerformance\(\'(.+)\',(.+),(.+)\)')
        is_special = "1" if is_special == "true" else "0"
        is_reserved = "1" if is_reserved == "true" else "0"
        # extract parameter from form
        display_id = response.xpath(
            '//form[@name="form2"]/input[@name="displayID"]/@value'
        ).extract_first()
        site_id = response.xpath(
            '//form[@name="form2"]/input[@name="siteID"]/@value'
        ).extract_first()

        request = scrapy.FormRequest.from_response(
            response, formxpath='//form[@name="form2"]',
            formdata={
                'JobID': 'pc.1.check.agreement',
                'performanceID': performance_id,
                'dt': '',
                'siteID': site_id,
                'isSpecial': is_special,
                'isReserved': is_reserved,
                'displayID': display_id
            }, callback=self.parse_agreement)
        # replace with real action generated by javascript
        theater_id = site_id
        page_id = "pc0005" if is_special == "1" else "pc0006"
        url = "https://cinema.aeoncinema.com/wm/app?theaterID={theater_id}"\
              "&selectedSiteId={site_id}&pageID={page_id}"\
              "&theaterID={theater_id}".format(
                  theater_id=theater_id, site_id=site_id, page_id=page_id)
        request = request.replace(url=url)
        return request

    def parse_agreement(self, response):
        # extract form action url
        script_text = response.xpath(
            '//script[contains(.,"pc.1.selectPerformance")]/text()'
            ).extract_first()
        match = re.search(r'\"(.+selectedSiteId=.+)\";', script_text)
        action = match.group(1)
        display_id = response.xpath(
            '//input[@name="displayID"]/@value').extract_first()
        url = self.generate_ticket_page_url(self, action, display_id)
        request = scrapy.Request(
            url, method='POST', callback=self.parse_normal_showing)
        request.meta["data_proto"] = response.meta["data_proto"]
        yield request

    def generate_ticket_page_url(self, response, action, display_id):
        return 'https://cinema.aeoncinema.com/wm/{action}'\
               '&JobID=pc.1.selectPerformance&agreement=yes'\
               '&displayID={display_id}'.format(
                   action=action, display_id=display_id)

    def parse_normal_showing(self, response):
        """
        go to json data url
        """
        url = response.xpath(
            '//script[contains(@src,"pc.2.pinpoint.jsondata")]/@src'
        ).extract_first()
        url = response.urljoin(url)
        request = scrapy.Request(url, callback=self.parse_showing_json)
        request.meta["data_proto"] = response.meta["data_proto"]
        yield request

    def parse_showing_json(self, response):
        """
        extract showing info from json data
        """
        script_text = copy.deepcopy(response.text)
        script_text = re.sub(r'[\t\r\n]', '', script_text, re.DOTALL)
        script_text = re.sub(
            r'if\( typeof.+?{}}WMC_E_DATA = ', '', script_text, re.DOTALL)
        json_data = demjson.decode(script_text)
        result = response.meta["data_proto"]

        empty_seat_count = 0
        booked_seat_count = 0
        locked_seat_count = 0
        for i in range(len(json_data['SeatMaps']['FLAG'][0])):
            for j in range(len(json_data['SeatMaps']['FLAG'][0][i])):
                curr_num = json_data['SeatMaps']['FLAG'][0][i][j]
                if curr_num == '1':
                    empty_seat_count += 1
                elif curr_num == '3':
                    booked_seat_count += 1
                elif curr_num == '8':
                    locked_seat_count += 1
        total_seat_count = (empty_seat_count + booked_seat_count
                            + locked_seat_count)
        result['book_seat_count'] = booked_seat_count
        result['total_seat_count'] = total_seat_count
        result['record_time'] = arrow.now()
        result['source'] = self.name
        yield result
