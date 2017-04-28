"""
base class for spiders crawling cinema info as processes are usually
very similar, like: county->cinema->(detailed page)
"""
import re
import unicodedata
import scrapy
from scrapyproject.items import (CinemaLoader, standardize_cinema_name,
                                 standardize_screen_name)
from scrapyproject.utils import (CinemaDatabaseMixin,
                                 standardize_county_name,
                                 extract_seat_number)


class CinemaSpider(scrapy.Spider, CinemaDatabaseMixin):

    def __init__(self, *args, **kwargs):
        super(CinemaSpider, self).__init__(*args, **kwargs)
        if not hasattr(self, 'county_xpath'):
            self.county_xpath = '/invalid_path'
        if not hasattr(self, 'cinema_xpath'):
            self.cinema_xpath = '/invalid_path'
        if not hasattr(self, 'cinema_site_xpath'):
            self.cinema_site_xpath = '/invalid_path'
        if not hasattr(self, 'screen_text_xpath'):
            self.screen_text_xpath = '/invalid_path'
        if not hasattr(self, 'screen_pattern'):
            self.screen_pattern = r'$invalid_match^'
        if not hasattr(self, 'screen_name_pattern'):
            self.screen_name_pattern = r'$invalid_match^'
        if not hasattr(self, 'seat_number_pattern'):
            self.seat_number_pattern = r'$invalid_match^'

    def parse(self, response):
        """
        crawl county data
        """
        county_list = response.xpath(self.county_xpath)
        for county in county_list:
            if not self.is_county_crawl(county):
                continue
            county_name = county.xpath('.//text()').extract_first()
            county_name = standardize_county_name(county_name)
            url = county.xpath('./@href').extract_first()
            url = response.urljoin(url)
            request = scrapy.Request(url, callback=self.parse_county)
            request.meta['county_name'] = county_name
            yield request

    def is_county_crawl(self, county):
        return True

    def parse_county(self, response):
        """
        parse cinemas for each county
        """
        cinema_list = response.xpath(self.cinema_xpath)
        for curr_cinema in cinema_list:
            cinema_name = curr_cinema.xpath('./text()').extract_first()
            cinema_name = standardize_cinema_name(cinema_name)
            if not self.is_cinema_crawl(cinema_name):
                continue
            url = curr_cinema.xpath('./@href').extract_first()
            url = self.adjust_cinema_url(response.urljoin(url))
            request = scrapy.Request(url, callback=self.parse_cinema)
            request.meta['county_name'] = response.meta['county_name']
            request.meta['cinema_name'] = cinema_name
            yield request

    def is_cinema_crawl(self, cinema_name):
        return True

    def adjust_cinema_url(self, url):
        """
        adjust cinema page's url if needed
        """
        return url

    def parse_cinema(self, response):
        """
        parse cinema's info
        """
        cinema = CinemaLoader(response=response)
        cinema.context['cinema_name'] = response.meta['cinema_name']
        cinema.add_value('nemas', response.meta['cinema_name'])
        cinema.add_value('county', response.meta['county_name'])
        site = response.xpath(self.cinema_site_xpath).extract_first()
        if site:
            site = self.adjust_cinema_site(response, site)
            cinema.add_value('site', site)
        (cinema['screens'], cinema['screen_count'],
         cinema['total_seats']) = self.parse_screen_data(response, cinema)
        cinema['source'] = self.name
        yield cinema

    def adjust_cinema_site(self, response, site):
        """
        adjust cinema official site's url if needed
        """
        return site

    def parse_screen_data(self, response, cinema):
        screen_raw_texts = response.xpath(self.screen_text_xpath).extract()
        screen = {}
        screen_count = 0
        total_seats = 0
        pattern = re.compile(self.screen_pattern)
        for raw_text in screen_raw_texts:
            raw_text = unicodedata.normalize('NFKC', raw_text)
            if not pattern.match(raw_text):
                continue
            screen_name = pattern.sub(self.screen_name_pattern, raw_text)
            screen_name = standardize_screen_name(screen_name, cinema)
            # add cinema name into screen name to avoid conflict for
            # sub cinemas
            screen_name = response.meta['cinema_name'] + "#" + screen_name
            seat_str = pattern.sub(self.seat_number_pattern, raw_text)
            seat_count = extract_seat_number(seat_str)
            screen_count += 1
            total_seats += seat_count
            screen[screen_name] = str(seat_count)
        return screen, screen_count, total_seats
