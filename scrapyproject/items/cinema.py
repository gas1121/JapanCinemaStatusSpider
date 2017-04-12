# -*- coding: utf-8 -*-
import scrapy


class Cinema(scrapy.Item):
    names = scrapy.Field()
    county = scrapy.Field()
    company = scrapy.Field()
    site = scrapy.Field()
    screens = scrapy.Field()
    screen_count = scrapy.Field()
    total_seats = scrapy.Field()
    source = scrapy.Field()