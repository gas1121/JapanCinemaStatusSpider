# -*- coding: utf-8 -*-
import re
import unicodedata
import copy
import demjson
import arrow
import scrapy
from scrapyproject.showingspiders.showing_spider import ShowingSpider
from scrapyproject.models import Movie
from scrapyproject.items import (ShowingItem, ShowingBookingItem,
                                 standardize_cinema_name,
                                 standardize_screen_name)
from scrapyproject.utils import standardize_site_url, AeonUtil


class AeonSpider(ShowingSpider):
    """
    aeon spider.
    """
    name = "aeon"
    allowed_domains = ["www.aeoncinema.com", "cinema.aeoncinema.com"]
    start_urls = [
        'http://www.aeoncinema.com/theater/'
    ]

    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        'COOKIES_DEBUG': True
    }

    cinema_list = ['イオンシネマ板橋']

    def parse(self, response):
        """
        crawl theater list data first
        """
        theater_link_list = response.xpath(
            '//div[contains(@class,"area")]//dd//a')
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
        # get schedule url and replace date string
        schedule_url = response.xpath(
            '//a[contains(@href,"dt=")]/@href').extract_first()
        schedule_url = re.sub(
            r'&dt=\d+&', '&dt=' + self.date + '&', schedule_url)
        request = scrapy.Request(schedule_url,
                                 callback=self.parse_cinema_schedule)
        request.meta["cinema_name"] = response.meta['cinema_name']
        request.meta["cinema_site"] = response.meta['cinema_site']
        request.meta["schedule_url"] = schedule_url
        yield request

    def parse_cinema_schedule(self, response):
        data_proto = ShowingItem()
        data_proto['cinema_name'] = response.meta['cinema_name']
        data_proto["cinema_site"] = standardize_site_url(
            response.meta["cinema_site"], response.meta["cinema_name"])
        data_proto['source'] = self.name
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
        movie_data_proto['real_title'] = Movie.get_by_title(title)
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
        screen_name = curr_showing.xpath('./div[2]/a/text()').extract_first()
        screen_name = standardize_screen_name(screen_name,  showing_data_proto)
        showing_data_proto['screen'] = screen_name
        # when site ordering is stopped stop crawling
        site_status = curr_showing.xpath(
            './a/span[2]/text()').extract_first()
        if site_status == '予約停止中':
            return
        # handle free order seat type showings
        seat_type = curr_showing.xpath(
            './div[@class="icon"]//img/@alt').extract_first()
        showing_data_proto['seat_type'] = \
            AeonUtil.standardize_seat_type(seat_type)

        # query screen number from database
        showing_data_proto['total_seat_count'] = \
            self.get_screen_seat_count(showing_data_proto)
        # check whether need to continue crawl booking data or stop now
        if not self.crawl_booking_data:
            result_list.append(showing_data_proto)
            return

        booking_data_proto = ShowingBookingItem()
        booking_data_proto['showing'] = showing_data_proto
        book_status = curr_showing.xpath('./a/span/text()').extract_first()
        booking_data_proto['book_status'] = \
            AeonUtil.standardize_book_status(book_status)
        if (showing_data_proto['seat_type'] == 'FreeSeat' or
                booking_data_proto['book_status'] in ['SoldOut', 'NotSold']):
            # sold out or not sold
            status = booking_data_proto['book_status']
            booking_data_proto['book_seat_count'] = (
                showing_data_proto['total_seat_count']
                if status == 'SoldOut' else 0)
            booking_data_proto['record_time'] = arrow.now()
            booking_data_proto['minutes_before'] = \
                self.get_minutes_before(booking_data_proto)
            result_list.append(booking_data_proto)
            return
        else:
            # normal, generate request to showing page
            showing_request = self.generate_agreement_request(
                response=response, curr_showing=curr_showing)
            # go to shchedule page again to generate independent cookie
            # for each showing
            schedule_url = response.meta['schedule_url']
            request = scrapy.Request(
                schedule_url, dont_filter=True, callback=self.parse_new_cookie)
            request.meta["data_proto"] = booking_data_proto
            request.meta["showing_request"] = showing_request
            (performance_id, _, _) = self.extract_showing_parameters(
                curr_showing)
            request.meta["cookiejar"] = performance_id
            result_list.append(request)

    def extract_showing_parameters(self, curr_showing):
        """
        extract parameter from javascript action
        """
        # code example:
        # javascript:selectPerformance('1703211024055000603',false,true)
        script = curr_showing.xpath('./a/@href')
        performance_id, is_special, is_reserved = script.re(
            'selectPerformance\(\'(.+)\',(.+),(.+)\)')
        return (performance_id, is_special, is_reserved)

    def generate_agreement_request(self, response, curr_showing):
        """
        generate post request to agreement page
        """
        (performance_id, is_special,
         is_reserved) = self.extract_showing_parameters(curr_showing)
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
            response, dont_filter=True, formxpath='//form[@name="form2"]',
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

    def parse_new_cookie(self, response):
        """
        generate cookie for showing page to use
        """
        request = response.meta['showing_request']
        request.meta["data_proto"] = response.meta['data_proto']
        request.meta["cookiejar"] = response.meta["cookiejar"]
        yield request

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
        request = scrapy.Request(url, method='POST', dont_filter=True,
                                 callback=self.parse_normal_showing)
        request.meta["data_proto"] = response.meta["data_proto"]
        request.meta["cookiejar"] = response.meta["cookiejar"]
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
        request.meta["cookiejar"] = response.meta["cookiejar"]
        yield request

    def parse_showing_json(self, response):
        """
        extract showing info from json data
        """
        # TODO D-Box seat need check if handled right
        script_text = copy.deepcopy(response.text)
        script_text = re.sub(r'[\t\r\n]', '', script_text, re.DOTALL)
        script_text = re.sub(
            r'if\( typeof.+?{}}WMC_E_DATA = ', '', script_text, re.DOTALL)
        json_data = demjson.decode(script_text)
        result = response.meta["data_proto"]

        booked_seat_count = 0
        for i in range(len(json_data['SeatMaps']['FLAG'][0])):
            for j in range(len(json_data['SeatMaps']['FLAG'][0][i])):
                curr_num = json_data['SeatMaps']['FLAG'][0][i][j]
                if curr_num == '3':
                    booked_seat_count += 1
        result['book_seat_count'] = booked_seat_count
        result['record_time'] = arrow.now()
        result['minutes_before'] = self.get_minutes_before(result)
        yield result
