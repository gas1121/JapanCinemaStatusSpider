# -*- coding: utf-8 -*-
import unicodedata
import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import Identity, TakeFirst, MapCompose
from scrapyproject.models import Movie, Cinema
from scrapyproject.items import (standardize_cinema_name,
                                 standardize_screen_name)
from scrapyproject.utils import standardize_site_url


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


def cinema_site_in(value, loader_context):
    loader = loader_context.get('loader')
    return standardize_site_url(value, loader.get_output_value('cinema_name'))


def screen_name_in(value, loader_context):
    loader = loader_context.get('loader')
    return standardize_screen_name(
        value,  loader.get_output_value('cinema_name'))


class ShowingLoader(ItemLoader):
    default_item_class = Showing
    default_input_processor = Identity()
    default_output_processor = TakeFirst()

    cinema_name_in = MapCompose(lambda v: standardize_cinema_name(v))
    cinema_site_in = MapCompose(cinema_site_in)
    screen_name_in = MapCompose(screen_name_in)

    def add_title(self, title, title_en=None):
        title = title.strip()
        title = unicodedata.normalize('NFKC', title)
        self.add_value('title', title)
        self.add_value('title_en', title_en)
        self.add_value('real_title', Movie.get_by_title(title))

    def get_title_list(self):
        title = self.get_output_value('title')
        title_en = self.get_output_value('title_en')
        real_title = self.get_output_value('real_title')
        return filter(None, [title, title_en, real_title])

    def add_screen_seat_count(self):
        cinema_name = self.get_output_value('cinema_name')
        cinema_site = self.get_output_value('cinema_site')
        screen = self.get_output_value('screen')
        return Cinema.get_screen_seat_count(
                cinema_name=cinema_name, cinema_site=cinema_site,
                screen=screen)
