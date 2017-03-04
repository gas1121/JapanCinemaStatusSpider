# -*- coding: utf-8 -*-
import copy
import scrapy


class EigaCinemaSpider(scrapy.Spider):
    name = "eiga_cinema"
    allowed_domains = ["eiga.com"]
    start_urls = ['http://eiga.com']

    def parse(self, response):
        """
        crawl cinema data from http://eiga.com
        """
        print(response.text)