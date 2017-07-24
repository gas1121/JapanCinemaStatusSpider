# -*- coding: utf-8 -*-
import unicodedata
import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import Identity, TakeFirst, MapCompose


class Movie(scrapy.Item):
    title = scrapy.Field()
    current_cinema_count = scrapy.Field()


class MovieLoader(ItemLoader):
    default_item_class = Movie
    default_input_processor = Identity()
    default_output_processor = TakeFirst()

    title_in = MapCompose(lambda v: unicodedata.normalize('NFKC', v))
