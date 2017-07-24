# -*- coding: utf-8 -*-
import arrow
import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import Identity, TakeFirst
from crawler.items.showing import Showing


class ShowingBooking(scrapy.Item):
    showing = scrapy.Field(serializer=Showing)
    book_status = scrapy.Field()
    book_seat_count = scrapy.Field()
    minutes_before = scrapy.Field()
    record_time = scrapy.Field()


class ShowingBookingLoader(ItemLoader):
    default_item_class = ShowingBooking
    default_input_processor = Identity()
    default_output_processor = TakeFirst()

    def add_time_data(self):
        # TODO bug
        print("add_time_data")
        self.add_value('record_time', arrow.now())
        print(self.get_output_value('showing')['start_time'])
        print(self.get_output_value('record_time'))
        time_before = (
            self.get_output_value('showing')['start_time'] -
            self.get_output_value('record_time'))
        print("add_time_data 2")
        minutes_before = time_before.days*1440 + time_before.seconds//60
        self.add_value('minutes_before', minutes_before)

    def add_book_status(self, book_status, util):
        value = util.standardize_book_status(book_status)
        self.add_value('book_status', value)


def init_show_booking_loader(response, item=None):
    """
    init ShowingBookingLoader with optional ShowingBooking item
    """
    loader = ShowingBookingLoader(response=response)
    if item:
        loader.add_value(None, item)
    return loader
