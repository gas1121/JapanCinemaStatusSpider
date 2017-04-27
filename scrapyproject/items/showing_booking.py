# -*- coding: utf-8 -*-
import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import Identity, TakeFirst, MapCompose
from scrapyproject.items.showing import Showing


class ShowingBooking(scrapy.Item):
    showing = scrapy.Field(serializer=Showing)
    book_status = scrapy.Field()
    book_seat_count = scrapy.Field()
    minutes_before = scrapy.Field()
    record_time = scrapy.Field()


class ShowingBookingLoader(ItemLoader):
    default_item_class = ShowingBooking()
    default_input_processor = Identity()
    default_output_processor = TakeFirst()
    # TODO
