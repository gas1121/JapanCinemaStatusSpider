# -*- coding: utf-8 -*-
import scrapy
from scrapyproject.items.showing import Showing


class ShowingBooking(scrapy.Item):
    showing = Showing()
    book_status = scrapy.Field()
    book_seat_count = scrapy.Field()
    record_time = scrapy.Field()
