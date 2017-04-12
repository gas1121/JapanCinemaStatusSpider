# -*- coding: utf-8 -*-
import scrapy


class Showing(scrapy.Item):
    title = scrapy.Field()
    title_en = scrapy.Field()
    start_time = scrapy.Field()
    end_time = scrapy.Field()
    cinema_name = scrapy.Field()
    cinema_site = scrapy.Field()
    screen = scrapy.Field()
    seat_type = scrapy.Field()
    total_seat_count = scrapy.Field()
    source = scrapy.Field()
