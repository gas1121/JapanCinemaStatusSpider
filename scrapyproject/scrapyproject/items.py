# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class Cinema(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    name = scrapy.Field()
    screens = scrapy.Field()


class Session(scrapy.Item):
    title = scrapy.Field()
    title_en = scrapy.Field()
    country = scrapy.Field()
    start_time = scrapy.Field()
    end_time = scrapy.Field()
    cinema_name = scrapy.Field()
    screen = scrapy.Field()
    book_status = scrapy.Field()
    book_data = scrapy.Field()
    record_time = scrapy.Field()
