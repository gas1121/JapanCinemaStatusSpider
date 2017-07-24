# -*- coding: utf-8 -*-
import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import Identity, TakeFirst, MapCompose
from scrapyproject.utils import standardize_site_url


class Cinema(scrapy.Item):
    names = scrapy.Field()
    county = scrapy.Field()
    company = scrapy.Field()
    site = scrapy.Field()
    screens = scrapy.Field()
    screen_count = scrapy.Field()
    total_seats = scrapy.Field()
    source = scrapy.Field()


def site_in(value, loader_context):
    cinema_name = loader_context.get('cinema_name')
    value = standardize_site_url(value, cinema_name)
    return value


class CinemaLoader(ItemLoader):
    default_item_class = Cinema
    default_input_processor = Identity()
    default_output_processor = TakeFirst()

    names_out = Identity()
    site_in = MapCompose(site_in)
