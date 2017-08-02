# -*- coding: utf-8 -*-
import re
import unicodedata
import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import Identity, TakeFirst
# TODO models rework
#from crawler.models import Movie, Cinema
from crawler.items import (standardize_cinema_name, standardize_screen_name)
from crawler.utils import standardize_site_url


class Showing(scrapy.Item):
    title = scrapy.Field()
    title_en = scrapy.Field()
    real_title = scrapy.Field()
    start_time = scrapy.Field()
    end_time = scrapy.Field()
    cinema_name = scrapy.Field()
    cinema_site = scrapy.Field()
    screen = scrapy.Field()
    seat_type = scrapy.Field()
    total_seat_count = scrapy.Field()
    source = scrapy.Field()


class ShowingLoader(ItemLoader):
    default_item_class = Showing
    default_input_processor = Identity()
    default_output_processor = TakeFirst()

    def add_cinema_name(self, cinema_name):
        self.add_value('cinema_name', standardize_cinema_name(cinema_name))

    def replace_cinema_name(self, cinema_name):
        self.replace_value('cinema_name', standardize_cinema_name(cinema_name))

    def add_cinema_site(self, cinema_site, cinema_name):
        self.add_value('cinema_site',
                       standardize_site_url(cinema_site, cinema_name))

    def add_screen_name(self, screen_name):
        cinema_name = self.get_output_value('cinema_name')
        self.add_value('screen',
                       standardize_screen_name(screen_name, cinema_name))

    def add_title(self, title, title_en=None):
        # normalize title to avoid full width characters
        title = re.sub(r'[\t\r\n]', '', title, re.DOTALL)
        title = title.strip()
        title = unicodedata.normalize('NFKC', title)
        if title_en:
            title_en = re.sub(r'[\t\r\n]', '', title_en, re.DOTALL)
            title_en = title_en.strip()
            title_en = unicodedata.normalize('NFKC', title_en)
        self.add_value('title', title)
        self.add_value('title_en', title_en)
        # TODO models rework
        #self.add_value('real_title', Movie.get_by_title(title))

    def get_title_list(self):
        title = self.get_output_value('title')
        title_en = self.get_output_value('title_en')
        real_title = self.get_output_value('real_title')
        return list(filter(None, [title, title_en, real_title]))

    def add_total_seat_count(self):
        cinema_name = self.get_output_value('cinema_name')
        cinema_site = self.get_output_value('cinema_site')
        screen = self.get_output_value('screen')
        # TODO models rework
        """
        self.add_value('total_seat_count', Cinema.get_screen_seat_count(
                cinema_name=cinema_name, cinema_site=cinema_site,
                screen=screen))
        """
