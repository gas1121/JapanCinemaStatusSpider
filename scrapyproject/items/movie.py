# -*- coding: utf-8 -*-
import scrapy


class Movie(scrapy.Item):
    title = scrapy.Field()
    site = scrapy.Field()
