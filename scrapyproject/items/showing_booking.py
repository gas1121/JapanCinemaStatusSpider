# -*- coding: utf-8 -*-
import arrow
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


def book_status_in(value, loader_context):
    value = loader_context.get('util').standardize_book_status(value)
    return value


class ShowingBookingLoader(ItemLoader):
    default_item_class = ShowingBooking
    default_input_processor = Identity()
    default_output_processor = TakeFirst()

    book_status_in = MapCompose(book_status_in)

    def add_time_data(self):
        self.add_value('record_time', arrow.now())
        time_before = (
            self.get_output_value('showing')['start_time'] -
            self.get_output_value('record_time'))
        minutes_before = time_before.days*1440 + time_before.seconds//60
        self.add_value('minutes_before', minutes_before)
