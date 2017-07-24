# -*- coding: utf-8 -*-
import re
import unicodedata
import copy
import demjson
import scrapy
from crawler.showingspiders.showing_spider import ShowingSpider
from crawler.items import (ShowingLoader, init_show_booking_loader)
from crawler.utils import AeonUtil


class AeonSpider(ShowingSpider):
    """
    aeon spider.
    """
    name = "aeon"
    allowed_domains = ["www.aeoncinema.com", "cinema.aeoncinema.com"]
    start_urls = [
        'http://www.aeoncinema.com/theater/',
    ]

    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
    }

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
            data_proto = ShowingLoader(response=response)
            data_proto.add_cinema_name(cinema_name)
            cinema_name = data_proto.get_output_value('cinema_name')
            if not self.is_cinema_crawl([cinema_name]):
                continue
            curr_cinema_url = theater_link.xpath('./@href').extract_first()
            curr_cinema_url = response.urljoin(curr_cinema_url)
            data_proto.add_cinema_site(curr_cinema_url, cinema_name)
            data_proto.add_value('source', self.name)
            request = response.follow(curr_cinema_url,
                                      callback=self.parse_cinema)
            request.meta["data_proto"] = data_proto.load_item()
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
        request = response.follow(schedule_url,
                                  callback=self.parse_cinema_schedule)
        request.meta["data_proto"] = response.meta['data_proto']
        request.meta["schedule_url"] = schedule_url
        yield request

    def parse_cinema_schedule(self, response):
        data_proto = ShowingLoader(response=response)
        data_proto.add_value(None, response.meta["data_proto"])
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
        title = curr_movie.xpath(
            './div[1]/p[1]/span/preceding::*[1]/text()').extract_first()
        if not title:
            title = curr_movie.xpath('./div[1]/p[1]/text()').extract_first()
        title_en = curr_movie.xpath(
            './div[1]/p[1]/span/text()').extract_first()
        movie_data_proto = ShowingLoader(response=response)
        movie_data_proto.add_value(None, data_proto.load_item())
        movie_data_proto.add_title(title=title, title_en=title_en)
        title_list = movie_data_proto.get_title_list()
        if not self.is_movie_crawl(title_list):
            return
        show_section_list = curr_movie.xpath('./div[2]/div')
        for curr_showing in show_section_list:
            self.parse_showing(response, curr_showing,
                               movie_data_proto, result_list)

    def parse_showing(self, response, curr_showing, data_proto, result_list):
        def parse_time(time_str):
            time_str = unicodedata.normalize('NFKC', start_time)
            time = time_str.split(":")
            return (int(time[0]), int(time[1]))

        # showing section passed in may be unusable and need to be filtered
        time_section = curr_showing.xpath('./div[@class="time"]')
        if not time_section:
            return
        showing_data_proto = ShowingLoader(response=response)
        showing_data_proto.add_value(None, data_proto.load_item())
        start_time = time_section.xpath('./span/span/text()').extract_first()
        start_hour, start_minute = parse_time(start_time)
        showing_data_proto.add_value('start_time', self.get_time_from_text(
            start_hour, start_minute))
        end_time = time_section.xpath('./span/text()').extract_first()
        end_hour, end_minute = parse_time(end_time)
        showing_data_proto.add_value('end_time', self.get_time_from_text(
            end_hour, end_minute))
        screen_name = curr_showing.xpath('./div[2]/a/text()').extract_first()
        showing_data_proto.add_screen_name(screen_name)
        # when site ordering is stopped stop crawling
        site_status = curr_showing.xpath(
            './a/span[2]/text()').extract_first()
        if site_status == '予約停止中':
            return
        # handle free order seat type showings
        seat_type = curr_showing.xpath(
            './div[@class="icon"]//img/@alt').extract_first()
        showing_data_proto.add_value(
            'seat_type', AeonUtil.standardize_seat_type(seat_type))

        # query screen number from database
        showing_data_proto.add_total_seat_count()
        # check whether need to continue crawl booking data or stop now
        if not self.crawl_booking_data:
            result_list.append(showing_data_proto.load_item())
            return

        booking_data_proto = init_show_booking_loader(response=response)
        booking_data_proto.add_value('showing', showing_data_proto.load_item())
        book_status = curr_showing.xpath('./a/span/text()').extract_first()
        booking_data_proto.add_book_status(book_status, util=AeonUtil)
        book_status = booking_data_proto.get_output_value('book_status')
        seat_type = showing_data_proto.get_output_value('seat_type')
        if (seat_type == 'FreeSeat' or book_status in ['SoldOut', 'NotSold']):
            # sold out or not sold
            total_seat_count = showing_data_proto.get_output_value(
                'total_seat_count')
            book_seat_count = (
                total_seat_count if book_status == 'SoldOut' else 0)
            booking_data_proto.add_value('book_seat_count', book_seat_count)
            booking_data_proto.add_time_data()
            result_list.append(booking_data_proto.load_item())
            return
        else:
            # normal, generate request to showing page
            showing_request = self.generate_agreement_request(
                response=response, curr_showing=curr_showing)
            # go to shchedule page again to generate independent cookie
            # for each showing
            schedule_url = response.meta['schedule_url']
            request = response.follow(
                schedule_url, dont_filter=True, callback=self.parse_new_cookie)
            request.meta["data_proto"] = booking_data_proto.load_item()
            request.meta["showing_request"] = showing_request
            (performance_id, _, _) = self.extract_showing_parameters(
                curr_showing)
            # add spider name to avoid conflict between spiders
            request.meta["cookiejar"] = self.name + performance_id
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
        request = response.follow(url, method='POST', dont_filter=True,
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
        request = response.follow(url, callback=self.parse_showing_json)
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
        result = init_show_booking_loader(
            response=response, item=response.meta["data_proto"])

        booked_seat_count = 0
        for i in range(len(json_data['SeatMaps']['FLAG'][0])):
            for j in range(len(json_data['SeatMaps']['FLAG'][0][i])):
                curr_num = json_data['SeatMaps']['FLAG'][0][i][j]
                if curr_num == '3':
                    booked_seat_count += 1
        result.add_value('book_seat_count', booked_seat_count)
        result.add_time_data()
        yield result.load_item()
